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

class SingleLocation:
    def __init__(self, type, address, geolocator):
        self.type = type
        self.address = address
        self.geolocator = geolocator
        
        geocode = RateLimiter(geolocator.geocode, min_delay_seconds = 1)
        location = geocode(address)
        self.lat = location.latitude
        self.long = location.longitude

class BaseKCPlaces:
    # this class serves as the base for the specific types of locations (e.g.
    # schools, grocery stores) that will be considered by the searching alg
    def __init__(self, place_type, origin):
        self.place_type = place_type
        self.client = googlemaps.Client(key = 'AIzaSyAGc-ZGZ3X4AU03AGWyhhCkPVd3OrC_V30')
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

    def collectAddressesForOnePage(self, list_of_elements):
        property_addresses = []
        for element in list_of_elements:
            address = element.get_property("title") 
            try:
                place_obj = SingleLocation(self.place_type, address, self.geolocator)
                property_addresses.append(place_obj)
            except AttributeError:
                print('{} could not be geocoded'.format(address))

        return property_addresses

    def checkValidAddress(self, address):
        beginning_condition = re.match(r'^[0-9]', address)
        end_condition = re.match(r'\d{5}$', address)
        if (beginning_condition and end_condition):
            return True
        else:
            return False

    def makeListOfPlaces(self):
        chrome_browser = WD.Chrome(ChromeDriverManager().install())
        chrome_browser.get("https://www.apartments.com/kansas-city-mo/1-bedrooms/")
        page_range_sentence = chrome_browser.find_element(By.CLASS_NAME, "pageRange").text
        page_numbers = int(re.findall('of.*', page_range_sentence)[0][2:])

        self.list_of_places = []
        for i in range(1, page_numbers + 1):
            chrome_browser.get("https://www.apartments.com/kansas-city-mo/1-bedrooms/{}".format(i))
            property_address_elements = chrome_browser.find_elements(By.CLASS_NAME, "property-address")
            page_list_of_locations = self.collectAddressesForOnePage(property_address_elements)
            self.list_of_places += page_list_of_locations

def rangeSearch(anchor, other, radius = 3000):
    X_anchor = anchor[['Latitude', 'Longitude']].applymap(radians)
    X_other = other[['Latitude', 'Longitude']].applymap(radians)
    earth_radius_meters = 6.378e+6

    tree = BallTree(X_other, metric = 'haversine')
    query = tree.query_radius(X_anchor, radius/earth_radius_meters, return_distance = True)
    
    return query

def generateCSVFiles():
    grocery = Groceries()
    grocery.makeListOfPlaces()
    grocery.sendListToCSV(overwrite = True)

    schools = Schools()
    schools.makeListOfPlaces()
    schools.sendListToCSV(overwrite = True)

def walkingDistanceMatrixRaw(l1, l2):
    client = googlemaps.Client(key = 'AIzaSyAGc-ZGZ3X4AU03AGWyhhCkPVd3OrC_V30')
    now = datetime(2023, 1, 14, 12)
    distance_matrix = pd.DataFrame([])
    for loc1 in l1:
        for loc2 in l2:
            distance = client.distance_matrix(loc1,
                                        loc2,
                                        mode = "walking",
                                        departure_time = now
                                        )['rows'][0]['elements'][0]['duration']['value']
            distance_matrix.loc[loc1, loc2] = distance/60
    
    return distance_matrix

def searchForOptimalApartments(groups: list, anchor, threshold):

    list_of_csv_files_in_dir = [file for file in os.listdir() if file.endswith('.csv')]
    if not len(list_of_csv_files_in_dir) > 0:
        for property_type in groups:
            property_type.makeListOfPlaces()
            property_type.sendListToCSV()
        searchForOptimalApartments(groups)

    list_of_csv_files_in_dir_no_anchor = [file for file in list_of_csv_files_in_dir.copy() if not anchor.place_type in file]
    list_of_all_properties = [list(pd.read_csv(file).columns) for file in list_of_csv_files_in_dir_no_anchor]
    anchor_properties = list(pd.read_csv(list(set(list_of_csv_files_in_dir).difference(set(list_of_csv_files_in_dir_no_anchor)))[0]).columns)
    while len(list_of_all_properties) > 0:
        pn = list_of_all_properties.pop()
        distance_matrix = walkingDistanceMatrix(anchor_properties, pn)
        print(distance_matrix)

def rangeSearchTest():
    X = np.random.random_sample((10, 2))
    y = np.random.random_sample((6, 2))

    tree = BallTree(X, metric = 'euclidean')
    matches = tree.query_radius(y, 0.2)
    
    fig, ax = plt.subplots()
    ax.scatter(X[:, 0], X[:, 1], color = 'green', alpha = 0.25)
    ax.scatter(y[:, 0], y[:, 1], color = 'blue', alpha = 0.25)
    for i, (x_coord, y_coord) in enumerate(zip(y[:, 0], y[:, 1])):
        circ = plt.Circle((x_coord, y_coord), 0.2, fill = False)
        ax.add_patch(circ)
        ax.scatter(X[:, 0][matches[i]], X[:, 1][matches[i]], s = 1, color = 'blue')
    # plt.scatter(y[matches], color = 'blue')
    ax.set_aspect('equal', adjustable='datalim')
    plt.show()

if __name__ == "__main__":
    pass
    pass