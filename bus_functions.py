# get bus route for each bus service

import pandas as pd
import osmnx as ox
from datetime import datetime
from datetime import timedelta
import pandas as pd
from shapely.geometry import Point, Polygon
import folium
import numpy as np
from math import radians, sin, cos, sqrt, atan2


def bus_stops_finder(bus_number, trips_df, stops_df,stop_times_df ):
    '''
    This function finds all available bus stops based on a bus number

    Inputs: 
    - bus_number (integer): Bus number 
    - trips_df: dataframe of trips.txt from GTFS data
    - stops_df: dataframe of stops.txt from GTFS data
    - stop_times_df: dataframe of stops_times.txt from GTFS data

    Outputs:
    - unique_stops: Array of unique bus stops in that bus line

    '''

    route_trips = trips_df[trips_df['route_id'].isin([bus_number])]

    # By getting the unique trip headsigns we can get a trip_id that is associate to the unique trips the bus makes. A bus makes multiple duplicate trips throughout the day, but the trip_headsign remains the same
    unique_rows = route_trips.drop_duplicates(subset='trip_headsign')

    bus_trip_id= unique_rows[['trip_id','direction_id']]

    # Using the bus IDs, we can filter out the stop times for each bus unqiue bus route with the stop_times_df
    selected_stop_times = stop_times_df[stop_times_df['trip_id'].isin(bus_trip_id['trip_id'])]
    selected_stop_times = selected_stop_times.merge(bus_trip_id, on="trip_id")

    # merge into one dataframe so we can get the bus locations and bus timings
    selected_stops_times_location = selected_stop_times.merge(stops_df[['stop_name', 'stop_lat', 'stop_lon','stop_id']], on='stop_id', how='inner')

    # get unique stops to display for user
    unique_stops = selected_stops_times_location['stop_name'].unique()

    unique_stops = unique_stops.tolist()

    return unique_stops, selected_stops_times_location


def bus_n_stops_finder(stop_times_df, trips_df,stops_df, user_latitude, user_longitude):

    # Merge relevant data
    merged_df = pd.merge(stop_times_df, trips_df, on='trip_id')
    merged_df = pd.merge(merged_df, stops_df, on='stop_id')

    # Extract unique bus stops with their coordinates and bus numbers
    unique_stops_routes = merged_df[['route_id', 'stop_name', 'stop_lat', 'stop_lon']].drop_duplicates()
    unique_stops = unique_stops_routes[[ 'stop_name', 'stop_lat', 'stop_lon']].drop_duplicates()
    # Define your specific location coordinates (latitude and longitude)

    # Calculate distances using Haversine formula
    def haversine(lat1, lon1, lat2, lon2):
        R = 6371  # Radius of the Earth in kilometers
        dlat = radians(lat2 - lat1)
        dlon = radians(lon2 - lon1)
        a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        distance = R * c
        return distance

    # Calculate distances for each bus stop
    unique_stops['distance'] = unique_stops.apply(lambda row: haversine(user_latitude, user_longitude, row['stop_lat'], row['stop_lon']), axis=1)

    # Sort bus stops by distance and get the closest stops
    closest_stops = unique_stops.nsmallest(3, 'distance')[[ 'stop_name', 'stop_lat', 'stop_lon', 'distance']]

    # Print or use the closest bus stops
    top3_stops = closest_stops['stop_name']

    bus_n_stops = unique_stops_routes[unique_stops_routes['stop_name'].isin(top3_stops)].merge(closest_stops, how = "left", on='stop_name')[['route_id','stop_name','distance']]

    bus_n_stops = bus_n_stops.sort_values(by='route_id')
    bus_n_stops['distance'] = (np.ceil(bus_n_stops['distance']*100 ) * 10).astype(int)
    bus_n_stops = bus_n_stops.rename(columns={'distance': 'distance (m)'})
    return bus_n_stops

def real_bus_origin(time, df, origin):
    '''
    Because the bus origin might change depending on the time the user departs, it is important to choose the user's bus
    stop correctly

    inputs:
    time: user inputs what time they wish to leave home
    df: this dataframe contains all the stop times and locations of the bus that the user selected
    user_origin: where the user intends to start from. user selected this on the stops.html page
    
    output: time appropriate bus stop
    '''
    time = str(time)
    str_time = time + ':00'

    origin_sequence = df[df['stop_name'] == origin ]
    last_sequence = max(df['stop_sequence'])
    min_time = timedelta(seconds=86400)

    print(origin)

    for index_origin, row_origin in origin_sequence.iterrows():
        min_sequence = row_origin['stop_sequence']
        if min_sequence <= last_sequence:

            # reset the first sequence  
            last_sequence = min_sequence

            # calculate the time difference
            start_time = datetime.strptime(row_origin['arrival_time'], '%H:%M:%S')
            user_time = datetime.strptime(str_time, '%H:%M:%S')
            time_diff = user_time - start_time
            # if the time difference between start of bus line and user time is positive, choose that bus line 
            if time_diff > timedelta(seconds=0):
                time_diff = min_time
                real_origin = row_origin
            else:
                pass

    # get the trip ID and and which order is it in the list of bus stops
    selected_trip_id= real_origin['trip_id']
    selected_stop_seq = real_origin['stop_sequence']

    # find all possible bus stops the user can go to and (selected_stops_times_location['trip_id'] == selected_trip_id)
    possible_locations = df[(df['stop_sequence'] >= selected_stop_seq) & (df['trip_id'] == selected_trip_id)]

    return possible_locations

# Define a function to convert each polygon to its centroid point
def get_centroid(geom):
    return Point(geom.centroid)


def POI_getter(amenities, possible_locations):

    '''
    color scheme

    food: green
    community stuff: brown
    leisure: blue

    folium icon list: https://fontawesome.com/v4/icons/
    '''
    amenities_of_interest = {
        # food
        'cafe':['coffee','brown'],'bar':['beer','brown'],'restaurant':['cutlery','brown'],'pub':['beer','brown'],

        
        # social buildings
        'social_centre':['institution','blue'],'library':['book','blue'],'marketplace':['shopping-cart','blue'],
        'events_venue':['institution','blue'],'exhibition_centre':['institution','blue'],'place_of_worship':['institution','blue'],

        # places to chill
        'park' :['tree','green'],'music_venue':['music', 'black'],'cinema':['film','blue'],'theatre':['film','blue']

        # transportation
    }

    # Define amenities of interest
    amenities = list(amenities_of_interest.keys())
    amenity_tags = {'amenity': amenities}
    building_tags = {"building": "train_station"}


    # Create an empty DataFrame to store POIs
    poi_df = pd.DataFrame()

    # Iterate through the DataFrame
    for index, row in possible_locations.iterrows():
        latitude = row['stop_lat']
        longitude = row['stop_lon']
        center_point = (latitude,longitude)
        tags = {'amenity': amenities}

        # change the distance!
        try:
            G = ox.features_from_point(center_point, tags={**amenity_tags, **building_tags}, dist=150)
            G['busstop'] = row['stop_name'] 
            poi_df = pd.concat([poi_df, G], ignore_index=True)
        except ox._errors.InsufficientResponseError as e:
            pass
        
    # Filter the geodataframe based on the condition
    poi_df[['icon','color']] = poi_df['amenity'].apply(lambda x: pd.Series(amenities_of_interest[x]) if x in amenities_of_interest else pd.Series([None, None]))
    

    # Apply the function to the geometry column and create a new column of points
    poi_df['points'] = poi_df['geometry'].apply(get_centroid)
    # Display the resulting DataFrame with POIs
    return poi_df


def transit_duration(origin, destination, location_df):
    # get the bus timings
    get_on = location_df[location_df['stop_name'] == origin]['departure_time'].values[0]
    get_off = location_df[location_df['stop_name'] == destination]['departure_time'].values[0]

    # calculate the time difference
    start_time = datetime.strptime(get_on, '%H:%M:%S')
    user_time = datetime.strptime(get_off, '%H:%M:%S')
    time_diff = user_time - start_time
    time_diff_mins = round(time_diff.total_seconds() / 60)

    return time_diff_mins

def map_maker(origin_stop, lat,lon,all_busstops, poi_df, stop_times_df):
    # Create a Folium map centered on a specific location
    map = folium.Map(location=[lat, lon], zoom_start=12)
    folium.Marker(
        location = [lat, lon], 
        popup='Home',
        icon=folium.Icon(color='darkgreen' ,icon='home', prefix='fa')).add_to(map)
    
    for index, row in all_busstops.iterrows():
        poi_lat = row['stop_lat']
        poi_lon = row['stop_lon']
        
        # Add a marker for each row to the map
        folium.Marker(
            location = [poi_lat, poi_lon], 
            # popup=folium.Popup(popup_text, parse_html=True, max_width=300),
            icon=folium.Icon(color='black' ,icon='bus', prefix='fa')).add_to(map)

    # Iterate over the rows of the DataFrame
    for index, row in poi_df.iterrows():
        poi_lat = row.points.y
        poi_lon = row.points.x
        poi_busstop = str(row['busstop'])
        poi_name = row['name']
        poi_amenity = row['amenity']
        icon_name = row['icon']
        icon_color = row['color']
        time = transit_duration(origin_stop,poi_busstop,stop_times_df)
        # print(f'printing {poi_name}')
        
        popup_text = folium.Html(f"Closest bus stop: {poi_busstop}.<br>Name of POI: {poi_name}.<br>Type of POI: {poi_amenity}.<br>Bus journey: {time}.", script = True)

        # Add a marker for each row to the map
        folium.Marker(
            location = [poi_lat, poi_lon], 
            popup=folium.Popup(popup_text, parse_html=True, max_width=300),
            icon=folium.Icon(color=icon_color ,icon=icon_name, prefix='fa')).add_to(map)


    # Display the map
    map.save('D:/Coding projects/Bus POI Finder/capmetro/templates/map.html')  # Save the map as an HTML file