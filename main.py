from utils import *

school_df = pd.read_csv('high school_properties.csv')
grocery_df = pd.read_csv('grocery store_properties.csv')
apartments_df = pd.read_csv('apartments.csv')

grocery_icon_url = "https://raw.githubusercontent.com/TheKenster1729/KC-Home-Finder/master/Pictures/image_processing20200903-25086-15xddqw.png"
grocery_icon_data = {"url": grocery_icon_url,
    "width": 242,
    "height": 242,
    "anchorY": 242,
}
grocery_df['icon_data'] = [grocery_icon_data] * len(grocery_df)

school_icon_url = "https://raw.githubusercontent.com/TheKenster1729/KC-Home-Finder/master/Pictures/1024px-Round_Landmark_School_Icon_-_Transparent.png"
school_icon_data = {"url": school_icon_url,
    "width": 242,
    "height": 242,
    "anchorY": 242,
}

apartment_icon_url = "https://raw.githubusercontent.com/TheKenster1729/KC-Home-Finder/master/Pictures/apartment.png"
apartment_icon_data = {"url": apartment_icon_url,
    "width": 242,
    "height": 242,
    "anchorY": 242,
}
apartments_df['icon_data'] = [apartment_icon_data] * len(apartments_df)

def flatten_array(array):
    unique_vals_array = np.array([])
    for el in array:
        unique_vals_array = np.append(unique_vals_array, el.ravel())
    
    return np.unique(unique_vals_array).astype(int)

def displayOptions(selected_schools, map, radius):
    # prepare the selected schools for a range search and initialize display
    selected_schools_df = school_df[school_df['Name'].isin(selected_schools)]
    selected_schools_df['icon_data'] = [school_icon_data] * len(selected_schools_df)
    addToFoliumMap(selected_schools_df, map)

    # apartments range search
    ind_apartments, _ = rangeSearch(selected_schools_df, apartments_df, radius = radius)
    unique_apartments_inds = flatten_array(ind_apartments)

    # initialize apartments display
    apartments_to_display = apartments_df.iloc[unique_apartments_inds]
    addToFoliumMap(apartments_to_display, map)

    # grocery range search
    ind_grocery, _ = rangeSearch(selected_schools_df, grocery_df, radius = radius)
    unique_grocery_inds = flatten_array(ind_grocery)

    # initialize grocery display
    groceries_to_display = grocery_df.iloc[unique_grocery_inds]
    addToFoliumMap(groceries_to_display, map)

if __name__ == "__main__":
    st.set_page_config(layout = 'wide')
    with st.form("select_schools"):
        label = 'Please select the school(s) you would like to see options for. Schools will be rendered as a pencil on the map.'
        selected_schools = st.multiselect(label, school_df['Name'])
        radius = st.slider("Select the radius (in meters) you'd like to search around each school.", max_value = 10000, step = 100,
                    value = 2000)
        submitted = st.form_submit_button("Submit")

        # TODO: center view on the centroid of all the selected schools
        if submitted:
            map = folium.Map(location = [39.097962363983996, -94.57958541684552], zoom_start = 12, tiles = "Stamen Terrain")
            displayOptions(selected_schools, map, radius = radius)
            st_folium(map, width = 1400, height = 700)