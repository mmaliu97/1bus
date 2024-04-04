from flask import Flask, render_template, request, jsonify, redirect, session, url_for
from bus_functions import *
import pandas as pd
from datetime import datetime
from datetime import timedelta
import simplejson as json
from flask_cors import CORS


app = Flask(__name__, template_folder="templates")
CORS(app)

app.secret_key = 'mliu'  # Set a secret key for session

stops_df = pd.read_csv("stops.csv")
trips_df = pd.read_csv("e_trips.csv")
stop_times_df = pd.read_csv("stop_times.csv")

@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    error_message = None

    result=[]
    if request.method == "POST":
        user_input = ""
        user_input = request.form.get("user_input")
        try:
            user_input = int(user_input)  # Try to convert input to a float
            result, stops_times_location_df = bus_stops_finder(user_input, trips_df, stops_df,stop_times_df)

            # Store the result in a session variable
            session['bus_stops'] = result
            session['bus'] = user_input

            # Redirect to the next page
            return redirect(url_for('stops_no_help', result=result))

        except ValueError:
            error_message = "Input is not a valid number."

    return render_template("index.html", result = result, error_message=error_message)

def get_busstops(bus_number, trips_df, stops_df,stop_times_df):
    bus_number = int(bus_number)
    result = bus_stops_finder(bus_number, trips_df, stops_df,stop_times_df)
    return result 


@app.route("/stops_no_help", methods=["GET", "POST"])
def stops_no_help():
    # Retrieve the result from the session variable
    result = session.get('bus_stops', [])
    bus = session.get('bus', [])
    df_json = session.get('my_dataframe')
    df = pd.read_json(df_json) if df_json else pd.DataFrame()
    if request.method == "POST":
        # get the user selection for bus stop
        
        bus_stop = ""
        bus_stop = request.form.get("bus_stop")

        time = request.form.get("time")

        result, stops_times_locations_df = bus_stops_finder(bus, trips_df, stops_df,stop_times_df)
        
        session['bus_stop'] = bus_stop
        all_busstops = real_bus_origin(time,stops_times_locations_df,bus_stop)
        amenities = ['restaurant', 'cafe', 'park','cinema','music_venue',
                'social_centre','theatre','marketplace']

        
        POI_df = POI_getter(amenities,all_busstops)

        # get lat, lng of original bus stop
        lat = stops_times_locations_df[stops_times_locations_df['stop_name'] == bus_stop].iloc[0]['stop_lat']
        lon = stops_times_locations_df[stops_times_locations_df['stop_name'] == bus_stop].iloc[0]['stop_lon']\
        
        map_maker(bus_stop, lat,lon,all_busstops,POI_df,stops_times_locations_df)
        # Redirect to the next page
        return redirect(url_for('poi'))
        # except ValueError:
        #     error_message = "Input is not a valid number."
    return render_template("stops_no_help.html", result=result, table=df.to_html(classes='table table-striped table-bordered'))

@app.route("/stops", methods=["GET", "POST"])
def stops():
    # Retrieve the result from the session variable
    result = session.get('bus_stops', [])
    bus = session.get('bus', [])
    df_json = session.get('my_dataframe')
    df = pd.read_json(df_json) if df_json else pd.DataFrame()
    if request.method == "POST":
        # get the user selection for bus stop
        
        bus_stop = ""
        bus_stop = request.form.get("bus_stop")

        time = request.form.get("time")

        result, stops_times_locations_df = bus_stops_finder(bus, trips_df, stops_df,stop_times_df)
        
        session['bus_stop'] = bus_stop
        all_busstops = real_bus_origin(time,stops_times_locations_df,bus_stop)
        amenities = ['restaurant', 'cafe', 'park','cinema','music_venue',
                'social_centre','theatre','marketplace']

        
        POI_df = POI_getter(amenities,all_busstops)

        # get lat, lng of original bus stop
        lat = stops_times_locations_df[stops_times_locations_df['stop_name'] == bus_stop].iloc[0]['stop_lat']
        lon = stops_times_locations_df[stops_times_locations_df['stop_name'] == bus_stop].iloc[0]['stop_lon']\
        
        map_maker(bus_stop, lat,lon,all_busstops,POI_df,stops_times_locations_df)
        # Redirect to the next page
        return redirect(url_for('poi'))
        # except ValueError:
        #     error_message = "Input is not a valid number."
    return render_template("stops.html", result=result, table=df.to_html(classes='table table-striped table-bordered'))

# @app.route('/prompt_location')
# def prompt_location():
#     return render_template('prompt_location.html')

@app.route('/get_data', methods=["GET",'POST'])
def get_data():
    try:
        # Get latitude and longitude from the request
        data = request.get_json()
        lat = float(data['latitude'])
        lon = float(data['longitude'])

        # Call your Python function with lat and lon
        result_df = bus_n_stops_finder(stop_times_df, trips_df,stops_df, lat, lon)
        print("i put redirection in")

        # Convert DataFrame to HTML table
        table_html = result_df.to_html(classes='table table-striped table-bordered')
        print(table_html)
        # Store DataFrame in session
        session['my_dataframe'] = result_df.to_json()
        # Render the HTML template with the DataFrame table
        return render_template('bus_info.html', table_html=table_html)
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
    
@app.route("/bus_info", methods=["GET",'POST'])
def bus_info():
    df_json = session.get('my_dataframe')

    df = pd.read_json(df_json) if df_json else pd.DataFrame()
    result=[]
    if request.method == "POST":
        user_input = ""
        user_input = request.form.get("user_input")
        try:
            user_input = int(user_input)  # Try to convert input to a float
            result, stops_times_location_df = bus_stops_finder(user_input, trips_df, stops_df,stop_times_df)

            # Store the result in a session variable
            session['bus_stops'] = result
            session['bus'] = user_input

            # Redirect to the next page
            return redirect(url_for('stops', result=result))

        except ValueError:
            error_message = "Input is not a valid number."

    return render_template('bus_info.html', table=df.to_html(classes='table table-striped table-bordered'))

@app.route("/poi")
def poi():
    return render_template("poi.html")

@app.route("/updates")
def updates():
    return render_template("updates.html")


if __name__ == '__main__':
    app.run(debug=True)



