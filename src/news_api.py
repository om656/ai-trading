import requests

class NewsAPI:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = 'https://newsapi.org/v2/'

    def get_top_headlines(self, country='us'):
        url = f'{self.base_url}top-headlines?country={country}&apiKey={self.api_key}'
        response = requests.get(url)
        return response.json()