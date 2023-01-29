from utils import *
import folium
from streamlit_folium import st_folium

school_df = pd.read_csv('high school_properties.csv')
grocery_df = pd.read_csv('grocery store_properties.csv')
apartments_df = pd.read_csv('apartment_properties.csv')

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

def displayOptions(selected_schools):
    # prepare the selected schools for a range search and initialize display
    selected_schools_df = school_df[school_df['Name'].isin(selected_schools)]
    selected_schools_df['icon_data'] = [school_icon_data] * len(selected_schools_df)
    layer_school = addIconLayer(selected_schools_df)

    # apartments range search
    ind_apartments, _ = rangeSearch(selected_schools_df, apartments_df, radius = 2000)
    unique_apartments_inds = flatten_array(ind_apartments)

    # initialize apartments display
    apartments_to_display = apartments_df.iloc[unique_apartments_inds]
    layer_apartments = addIconLayer(apartments_to_display, size = 3)

    # grocery range search
    ind_grocery, _ = rangeSearch(selected_schools_df, grocery_df, radius = 2000)
    unique_grocery_inds = flatten_array(ind_grocery)

    # initialize grocery display
    groceries_to_display = grocery_df.iloc[unique_grocery_inds]
    layer_grocery = addIconLayer(groceries_to_display)

    view_state = pdk.ViewState(
        longitude = -94.57717312400938,
        latitude = 39.109489416492714,
        zoom = 12,
        min_zoom = 5,
        max_zoom = 25)
    pydeck_chart = pydeck.Deck(layers = [layer_school, layer_apartments, layer_grocery], initial_view_state = view_state, tooltip = {"text": "{Address}"})    

def start_streamlit():
    with st.form("select_schools"):
        label = 'Please select the school(s) you would like to see options for.'
        selected_schools = st.multiselect(label, school_df['Name'])
        submitted = st.form_submit_button("Submit")

        if submitted:
            displayOptions(selected_schools)

m = folium.Map(location=[45.372, -121.6972], zoom_start=12, tiles="Stamen Terrain")

folium.Marker(
    location=[45.3288, -121.6625],
    popup="Mt. Hood Meadows",
    icon=folium.Icon(color = 'purple', icon = "shopping-cart"),
).add_to(m)

folium.Marker(
    location=[45.3311, -121.7113],
    popup="Timberline Lodge",
    icon=folium.Icon(icon="home"),
).add_to(m)

folium.Marker(
    location=[45.3300, -121.6823],
    popup="Some Other Location",
    icon=folium.Icon(color="red", icon="glyphicon-pencil"),
).add_to(m)

# call to render Folium map in Streamlit
st_data = st_folium(m, width=725)
