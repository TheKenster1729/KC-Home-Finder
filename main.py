from utils import *
import pydeck as pdk
import streamlit as st
import numpy as np
import pydeck

school_df = pd.read_csv('high school_properties.csv')
grocery_df = pd.read_csv('grocery store_properties.csv')
apartments_df = pd.read_csv('apartment_properties.csv')

icon_url = "https://raw.githubusercontent.com/TheKenster1729/KC-Home-Finder/master/Pictures/1024px-Round_Landmark_School_Icon_-_Transparent.png"
icon_data = {"url": icon_url,
    "width": 242,
    "height": 242,
    "anchorY": 242,
}
grocery_df['icon_data'] = [icon_data] * len(grocery_df)

def test_icons():
    # Data from OpenStreetMap, accessed via osmpy
    DATA_URL = "https://raw.githubusercontent.com/ajduberstein/geo_datasets/master/biergartens.json"
    ICON_URL = "https://raw.githubusercontent.com/TheKenster1729/KC-Home-Finder/master/Pictures/1024px-Round_Landmark_School_Icon_-_Transparent.png"

    icon_data = {
        # Icon from Wikimedia, used the Creative Commons Attribution-Share Alike 3.0
        # Unported, 2.5 Generic, 2.0 Generic and 1.0 Generic licenses
        "url": ICON_URL,
        "width": 242,
        "height": 242,
        "anchorY": 242,
    }

    data = pd.read_json(DATA_URL)
    data["icon_data"] = None
    for i in data.index:
        data["icon_data"][i] = icon_data

    print(data)
    view_state = pdk.data_utils.compute_view(data[["lon", "lat"]], 0.1)

    icon_layer = pdk.Layer(
        type="IconLayer",
        data=data,
        get_icon="icon_data",
        get_size=6,
        size_scale=15,
        get_position=["lon", "lat"],
        pickable=True,
    )

    r = pdk.Deck(layers=[icon_layer], initial_view_state=view_state, tooltip={"text": "{tags}"})
    st.pydeck_chart(r)

def displayOptions(selected_schools):
    selected_schools_df = school_df[school_df['Name'].isin(selected_schools)]
    ind_grocery, _ = rangeSearch(selected_schools_df, grocery_df)
    ind_apartments, _ = rangeSearch(selected_schools_df, apartments_df)
    layers = []
    # for i, school_name in enumerate(selected_schools):
    # grocery_stores = grocery_df.iloc[ind_grocery[i]]
    # grocery_stores['icon_data'] = [icon_data] * len(grocery_stores)
    # print(grocery_stores)
    layer = pdk.Layer(
        type = "IconLayer",
        data = grocery_df,
        get_icon = "icon_data",
        get_size = 6,
        size_scale = 15,
        get_position = ["Longitude", "Latitude"],
        pickable = True,
    )

    view_state = pdk.ViewState(
        longitude = -94.57717312400938,
        latitude = 39.109489416492714,
        zoom = 12,
        min_zoom = 5,
        max_zoom = 25)
    pydeck_chart = pydeck.Deck(layers = [layer], initial_view_state = view_state)
    st.pydeck_chart(pydeck_chart)

with st.form("select_schools"):
    label = 'Please select the school(s) you would like to see options for.'
    selected_schools = st.multiselect(label, school_df['Name'])
    submitted = st.form_submit_button("Submit")

    if submitted:
        displayOptions(selected_schools)