import googlemaps
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

def walkingDistanceMatrix(anchor, other):
    client = googlemaps.Client(key = 'AIzaSyAGc-ZGZ3X4AU03AGWyhhCkPVd3OrC_V30')
    now = datetime(2023, 1, 15, 12)
    distance_matrix = pd.DataFrame([])
    inds, dists = rangeSearch(anchor, other)
    for other_index, range_search_results in enumerate(inds):
        for anchor_index in range_search_results:
            anchor_property_address = anchor['Address'].iloc[anchor_index]
            other_property_address = other['Address'].iloc[other_index]                
            distance = client.distance_matrix(anchor_property_address,
                                        other_property_address,
                                        mode = "walking",
                                        departure_time = now
                                        )['rows'][0]['elements'][0]['duration']['value']
            distance_matrix.loc[anchor_property_address, other_property_address] = distance/60
            if anchor_property_address == '211 Linwood Blvd, Kansas City, MO 64111, United States':
                if other_property_address == '10 E 13th St, Kansas City, MO 64106, United States':
                    print(distance)

    return distance_matrix

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
    # school_df = pd.read_csv('high school_properties.csv')
    # grocery_df = pd.read_csv('grocery store_properties.csv')
    # apartments_df = pd.read_csv('apartment_properties.csv')

    #setting center for our map
    # center = [20.593684,78.96288]

    # creating map
    # map = folium.Map(location = center, zoom_start = 10)
    # for i, j in grocery_df.iterrows():
    #     location = [j['Latitude'], j['Longitude']]
    #     folium.Marker(location, popup = f'Grocery Store:{j["Address"]}').add_to(map)
    # map.save("tutorial.html")
    # map_df = grocery_df[['Latitude', 'Longitude']]
    # map_df = map_df.rename({'Latitude': 'lat', 'Longitude': 'lon'}, axis = 1)
    # st.map(map_df)
    # gdf = gp.GeoDataFrame(grocery_df, geometry = gp.points_from_xy(grocery_df.Longitude, grocery_df.Latitude))
    # print(gdf)
    # gdf.set_crs(epsg = 6922, inplace = True, allow_override = True)
    # m = gdf.explore()
    # m.save("figure_test.html")
    # print(gdf)
    # path_to_data = gp.datasets.get_path("nybb")
    # gdf = gp.read_file(path_to_data)
    # print(gdf)
    # gdf = gdf.set_index("BoroName")
    # gdf["area"] = gdf.area

    # m = gdf.explore("area")
    # m.save("tutorial.html")

    # other = pd.concat([school_df, grocery_df], join = 'inner')
    # ind, dists = rangeSearch(apartments_df, other)
    # for i, val in enumerate(ind):
    #     apartment = apartments_df.iloc[i]
    #     matches = other.iloc[val]
    #     if len(matches['Type'].unique()) == 2:            
    #         if (matches['Address'].str.startswith('301 E 51st St').any()) or (matches['Address'].str.startswith('241 Linwood Blvd').any()):
    #             print(apartment['Address'])
    #             print(matches[['Address', 'Type']])
    # # rangeSearchTest()
    # ind, results = rangeSearch(grocery_df, school_df)
    # grocery_property = 0
    # properties_in_range_indices = search[grocery_property]
    # properties_in_range = school_df.iloc[properties_in_range_indices]
    # print(properties_in_range)
    # searchForOptimalApartments([Schools(), Groceries(), Living()], Living(), 60)
    # locations1 = ['1444 Grand Blvd, Kansas City, MO 64106', '230 E 30th St, Kansas City, MO 64108', '5100 Oak St, Kansas City, MO 64112']
    # locations2 = ['10 E 13th St, Kansas City, MO 64106, United States', '640 E 18th St, Kansas City, MO 64108, United States', '310 E 5th St, Kansas City, MO 64106, United States', '2620 Independence Ave, Kansas City, MO 64124, United States', '201 Wyandotte St # 402, Kansas City, MO 64105, United States']
    # distance_matrix = walkingDistanceMatrix(school_df, grocery_df)
    # distance_matrix.to_csv('results.csv')

    # school_list = list(school_df['Address'])
    # grocery_list = list(grocery_df['Address'])
    # distance_matrix_raw = walkingDistanceMatrixRaw(grocery_list, school_list)
    # distance_matrix_raw.to_csv('results_raw.csv')
    # distance_matrix = distance_matrix[distance_matrix.apply(lambda x: x < 15)]

    # client = googlemaps.Client(key = 'AIzaSyAGc-ZGZ3X4AU03AGWyhhCkPVd3OrC_V30')
    # distance = client.distance_matrix('10 E 13th St, Kansas City, MO 64106, United States',
    #                                     '211 Linwood Blvd, Kansas City, MO 64111, United States',
    #                                     mode = "walking",
    #                                     departure_time = datetime(2023, 1, 14, 12)
    #                                     )['rows'][0]['elements'][0]['duration']['value']
    # print(distance)