from datetime import datetime
import requests
from bs4 import BeautifulSoup
from urllib.parse import unquote

url = 'https://www.apartments.com/kansas-city-mo/min-1-bedrooms/'
response = requests.get(unquote(url))
print(response.json)

soup = BeautifulSoup(response.content, 'html.parser')