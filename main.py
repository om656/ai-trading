import time
from news_api import NewsAPI
from trading_system import TradingSystem

API_KEY = '4ee32a25353049199a508620200f920c'
news_api = NewsAPI(API_KEY)
trading_system = TradingSystem(news_api)

while True:
    trading_system.trade_based_on_news()
    time.sleep(3600)  # Request news every hour