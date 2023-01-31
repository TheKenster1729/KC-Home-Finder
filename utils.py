from jsonpath import JSONPath
import pandas as pd
from selenium import webdriver as WD
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import regex as re
import os
from itertools import combinations, product
from datetime import datetime
import numpy as np
from sklearn.neighbors import BallTree
from geopy.extra.rate_limiter import RateLimiter
from geopy.geocoders import Nominatim
import matplotlib.pyplot as plt
from math import radians
import geopandas as gp
import pydeck as pdk
import streamlit as st
import numpy as np
import folium
from streamlit_folium import st_folium
import googlemaps

class SingleLocation:
    def __init__(self, type, address, geolocator):
        self.type = type
        self.address = address
        self.geolocator = geolocator
        
        geocode = RateLimiter(geolocator.geocode, min_delay_seconds = 1)
        location = geocode(address)
        self.lat = location.latitude
        self.long = location.longitude

class Apartment(SingleLocation):
    def __init__(self, url, rent, type, address, geolocator):
        super().__init__(type, address, geolocator)
        self.url = url
        self.rent = rent

class BaseKCPlaces:
    # this class serves as the base for the specific types of locations (e.g.
    # schools, grocery stores) that will be considered by the searching alg
    def __init__(self, place_type, origin):
        self.place_type = place_type
        self.client = googlemaps.Client(key = None)
        self.geolocator = Nominatim(user_agent = "Home_Finder")
        self.origin = origin

    # method to change the list of places in case it is obtained otherwise
    def changeListOfPlaces(self, new_list):
        self.list_of_places = new_list

    # checks to make sure address is valid using a proxy:
    # the address beings with a number and ends in 'United States'
    def checkValidAddress(self, address):
        beginning_condition = re.match(r'^[0-9]', address)
        end_condition = address[-13:] == 'United States'
        if (beginning_condition and end_condition):
            return True
        else:
            return False

    # communicates with gmaps API to find all places of a given type and stores
    # it in a list
    def makeListOfPlaces(self, radius = 1000):
        # TODO: better geocoder
        lat, long = self.client.geocode(self.origin)[0]['geometry']['location'].values()
        gmaps_search_result = self.client.places(self.place_type, (lat, long), radius = 12000)
        all_places_addresses = JSONPath('$..formatted_address').parse(gmaps_search_result)
        self.list_of_places = []
        for place in all_places_addresses:
            if self.checkValidAddress(place):
                try:
                    place_obj = SingleLocation(self.place_type, place, self.geolocator)
                except AttributeError:
                    print('{} could not be geocoded'.format(place))
                self.list_of_places.append(place_obj)

    def sendListToCSV(self, filename = None, overwrite = False):
        if not filename:
            filename = '{}_properties.csv'.format(self.place_type)

        if (os.path.exists(filename) and not overwrite):
            print('File exists, no new file created.')
        
        else:
            csv_df = pd.DataFrame([])
            csv_df['Address'] = [place.address for place in self.list_of_places]
            csv_df['Latitude'] = [place.lat for place in self.list_of_places]
            csv_df['Longitude'] = [place.long for place in self.list_of_places]
            csv_df['Type'] = [place.type for place in self.list_of_places]
            csv_df.to_csv(filename)

class Schools(BaseKCPlaces):
    def __init__(self):
        super().__init__('high school', 'Kansas City, MO')

class Groceries(BaseKCPlaces):
    def __init__(self):
        super().__init__('grocery store', 'Kansas City, MO')

class Living(BaseKCPlaces):
    # kept as same base class but uses Apartments.com for search
    def __init__(self):
        super().__init__('apartment', 'Kansas City, MO')

    def collectInfoForOnePage(self, list_of_address_elements, list_of_rent_elements, set_of_url_elements):
        list_of_url_elements = list(set_of_url_elements)
        for add, rent, url in zip(list_of_address_elements, list_of_rent_elements, list_of_url_elements):
            address = add.get_property("title")
            price = rent.text
            try:
                place_obj = Apartment(url, price, self.place_type, address, self.geolocator)
                row_to_add = pd.DataFrame(data = {"Address": [place_obj.address], "Longitude": [place_obj.long], 
                        "Latitude": [place_obj.lat], "Rent": [place_obj.rent], "URL": [place_obj.url], "Type": [place_obj.type]})
                self.places_database = pd.concat([self.places_database, row_to_add], ignore_index = True)
            except AttributeError:
                print('{} could not be geocoded'.format(address))

    def checkValidAddress(self, address):
        beginning_condition = re.match(r'^[0-9]', address)
        end_condition = re.match(r'\d{5}$', address)
        if (beginning_condition and end_condition):
            return True
        else:
            return False

    def getApartmentAttributes(self, browser, url):
        browser.get(url)
        # gets all the property addresses on this page
        property_addresses = browser.find_elements(By.CLASS_NAME, "property-address")
        # gets all the rents on this page
        property_prices_elements = browser.find_elements(By.CLASS_NAME, "property-pricing")
        # first step to getting all the links, but needs some polishing first
        property_links = browser.find_elements(By.CLASS_NAME, "property-link")
        property_links_unique = set([element.get_property("href") for element in property_links])

        return property_addresses, property_prices_elements, property_links_unique

    def makeListOfPlaces(self):
        chrome_browser = WD.Chrome(ChromeDriverManager().install())
        chrome_browser.get("https://www.apartments.com/kansas-city-mo/1-bedrooms/")
        page_range_sentence = chrome_browser.find_element(By.CLASS_NAME, "pageRange").text
        page_numbers = int(re.findall('of.*', page_range_sentence)[0][2:])

        self.places_database = pd.DataFrame(columns = ['Address', 'Longitude', 'Latitude', 'Rent', 'URL', 'Type'])
        for i in range(1, page_numbers + 1):
            url = "https://www.apartments.com/kansas-city-mo/1-bedrooms/{}".format(i)
            addresses, rents, urls = self.getApartmentAttributes(chrome_browser, url)
            # create an Apartment object after processing all the data
            self.collectInfoForOnePage(addresses, rents, urls)

    def sendListToCSV(self):
        self.places_database.to_csv("apartments.csv")

def generateCSVFiles():
    # grocery = Groceries()
    # grocery.makeListOfPlaces()
    # grocery.sendListToCSV(overwrite = True)

    # schools = Schools()
    # schools.makeListOfPlaces()
    # schools.sendListToCSV(overwrite = True)

    apartments = Living()
    apartments.makeListOfPlaces()
    apartments.sendListToCSV()

def rangeSearch(anchor, other, radius = 3000):
    X_anchor = anchor[['Latitude', 'Longitude']].applymap(radians)
    X_other = other[['Latitude', 'Longitude']].applymap(radians)
    earth_radius_meters = 6.378e+6

    tree = BallTree(X_other, metric = 'haversine')
    query = tree.query_radius(X_anchor, radius/earth_radius_meters, return_distance = True)
    
    return query

def addToFoliumMap(location_df, map):

    def createMarker(property_data):
        colors = {'elementary': 'red', 'middle': 'red', 'high': 'red', 'middle/high': 'red', 
            'elementary/middle/high': 'red', 'elementary/middle': 'red', 'pre-k': 'red',  'grocery store': 'purple', 'apartment': 'blue'}
        icons = {'elementary': 'pencil', 'middle': 'pencil', 'high': 'pencil', 'middle/high': 'pencil', 
            'elementary/middle/high': 'pencil', 'elementary/middle': 'pencil', 'pre-k': 'pencil',  'grocery store': 'shopping-cart', 
            'apartment': 'home'}
        if property_data.Type == 'apartment':
            popup = folium.Popup(f"""<p> {property_data.Address}<p>
                        <p>{property_data.Rent}</p>
                        <p><a href="{property_data.URL}" target="_blank">Link</a></p>
                        """,  max_width = 100
                    )
        else:
            popup = folium.Popup(property_data.Address, max_width = 100)
        folium.Marker(
            location = [property_data.Latitude, property_data.Longitude],
            popup = popup,
            icon = folium.Icon(color = colors[property_data.Type], icon = icons[property_data.Type]),
        ).add_to(map)

    location_df.apply(createMarker, axis = 1)
