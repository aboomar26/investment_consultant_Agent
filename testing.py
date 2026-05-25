import yfinance as yf
import chromadb
from tavily import TavilyClient
from dotenv import load_dotenv
import os

# stock = yf.Ticker("MSFT")
# print(stock.balance_sheet)
# print(stock.income_stmt)
# print(stock.cashflow)

#testing chromadb

# client = chromadb.Client()
# collection = client.create_collection(name="test_collection")
# print(collection)

# testing tavily
# load_dotenv()
# tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
# results = tavily_client.search("What is the current stock price of Microsoft?", top_k=1)
# print(results)
