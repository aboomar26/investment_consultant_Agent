import os
import requests
from dotenv import load_dotenv

load_dotenv()
FILINGS_DIR = os.getenv("FILINGS_DIR", "./data/filings")

# SEC EDGAR headers — required by SEC, use your own email
HEADERS = {
    "User-Agent": os.getenv("user_email"),
    "Accept-Encoding": "gzip, deflate",
    "Host": "data.sec.gov"
}

def get_cik(ticker: str) -> str:
    """Convert stock ticker to SEC CIK number."""
    url = "https://www.sec.gov/files/company_tickers.json"
    response = requests.get(url, headers=HEADERS)
    data = response.json()
    ticker_upper = ticker.upper()
    for entry in data.values():
        if entry["ticker"] == ticker_upper:
            return str(entry["cik_str"]).zfill(10)
    raise ValueError(f"Ticker {ticker} not found in SEC database")

def get_latest_filing_text(ticker: str, form_type: str = "10-K") -> dict:
    """
    Download the latest 10-K or 10-Q filing text for a ticker.
    Returns dict with text content and metadata.
    """
    os.makedirs(FILINGS_DIR, exist_ok=True)

    cik = get_cik(ticker)
    print(f"Found CIK for {ticker}: {cik}")

    # Get filing history
    submissions_url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    response = requests.get(submissions_url, headers=HEADERS)
    submissions = response.json()

    # Find most recent filing of the requested type
    filings = submissions["filings"]["recent"]
    forms = filings["form"]
    accession_numbers = filings["accessionNumber"]
    filing_dates = filings["filingDate"]

    filing_idx = None
    for i, form in enumerate(forms):
        if form == form_type:
            filing_idx = i
            break

    if filing_idx is None:
        raise ValueError(f"No {form_type} found for {ticker}")

    accession = accession_numbers[filing_idx].replace("-", "")
    filing_date = filing_dates[filing_idx]

    # Get the filing index to find the main document
    index_url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession}/{accession_numbers[filing_idx]}-index.json"
    index_response = requests.get(index_url, headers=HEADERS)

    # Download filing documents — look for the main HTML/TXT document
    filing_url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession}/"
    index_page = requests.get(
        f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik}&type={form_type}&dateb=&owner=include&count=1&search_text=",
        headers={"User-Agent": HEADERS["User-Agent"]}
    )

    # Simpler approach: use the EDGAR full-text search API
    search_url = f"https://efts.sec.gov/LATEST/search-index?q=%22{ticker}%22&dateRange=custom&startdt=2023-01-01&forms={form_type}"
    search_resp = requests.get(search_url, headers=HEADERS)

    # Direct approach: construct the filing text URL
    txt_url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession}/{accession_numbers[filing_idx]}.txt"
    txt_response = requests.get(txt_url, headers=HEADERS)

    # Clean the text (SEC filings contain a lot of HTML/XML)
    raw_text = txt_response.text
    # Remove HTML tags simply
    import re
    clean_text = re.sub(r'<[^>]+>', ' ', raw_text)
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()
    # Keep only the meaningful financial text (first 200k chars covers most filings)
    clean_text = clean_text[:200000]

    # Save to disk
    filepath = os.path.join(FILINGS_DIR, f"{ticker}_{form_type}_{filing_date}.txt")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(clean_text)

    print(f"Saved {form_type} for {ticker} ({filing_date}) to {filepath}")

    return {
        "ticker": ticker.upper(),
        "form_type": form_type,
        "filing_date": filing_date,
        "year": filing_date[:4],
        "filepath": filepath,
        "text": clean_text,
        "company_name": submissions.get("name", ticker),
        "cik": cik
    }