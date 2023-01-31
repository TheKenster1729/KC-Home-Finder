from utils import *

school_df = pd.read_csv('high school_properties.csv')
grocery_df = pd.read_csv('grocery store_properties.csv')
apartments_df = pd.read_csv('apartments.csv')

def flatten_array(array):
    unique_vals_array = np.array([])
    for el in array:
        unique_vals_array = np.append(unique_vals_array, el.ravel())
    
    return np.unique(unique_vals_array).astype(int)

def displayOptions(selected_schools, map, radius):
    # prepare the selected schools for a range search and initialize display
    selected_schools_df = school_df[school_df['Name'].isin(selected_schools)]
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

st.set_page_config(layout = 'wide')
with st.sidebar:
    st.header("Welcome to KC Home Finder!")
    st.markdown("The goal of this web app is to make it easier to find an apartment in \
        Kansas City, particularly if you're looking to live close to your school. The suggested \
        use is to select a school or schools you're interested in looking at from the dropdown menu \
        (each school is one of the TFA KC partner schools), select a radius around which you'd like to \
        search for apartments and grocery stores, and then explore using the generated map.")
    st.markdown("Right now, only grocery stores (shopping cart icon), schools (pencil icon), and apartments \
        (house icon) will display on the map, because those are the most important to me personally. But \
        if you'd like to see more features around each of the schools (e.g. cafes, restaurants), just let me know \
        and I can incorporate it without much trouble.")
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