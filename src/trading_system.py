class TradingSystem:
    def __init__(self, news_api):
        self.news_api = news_api

    def trade_based_on_news(self):
        headlines = self.news_api.get_top_headlines()
        # Implement trading logic based on headlines
        # Placeholder logic: print headlines
        for article in headlines['articles']:
            print(article['title'])