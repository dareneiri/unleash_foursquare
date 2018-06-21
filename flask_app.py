import os
import json
import requests
from datetime import datetime as dt
import time
from requests_oauthlib import OAuth2Session
from flask import Flask, request, redirect, render_template, session, url_for
import numpy as np
import pandas as pd


## Make changes here based on your developer.foursquare.com account
CLIENT_ID = 'ADD CLIENT ID'
CLIENT_SECRET = 'ADD CLIENT SECRET'
AUTHORIZATION_BASE_URL = 'https://foursquare.com/oauth2/authenticate'
TOKEN_URL = 'https://foursquare.com/oauth2/access_token'
REDIRECT_URI = 'https://YOUR_ACCOUNT_NAME.pythonanywhere.com/callback' # Change to whatever you want to call the function 

## Add Mapbox accessToken
MAPBOX_ACCESSTOKEN = 'ADD_TOKEN_MAPBOX'

## Additional parameters
CURRENT_DATE = dt.today().strftime('%Y%m%d')
FILETIME = str(time.time())
PATH = '/home/YOUR_ACCOUNT_NAME/downloads/' # I created this folder manually
FILENAME = 'foursquare-checkins-'+FILETIME+'.json'
FILENAME_CSV = 'foursquare-checkins-'+FILETIME+'.csv'
FILENAME_GEOJSON = 'heatmap-'+FILETIME+'.geojson'

DEBUG = False

app = Flask(__name__)
app.secret_key = os.urandom(50)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/test_fs', methods=['GET'])
def test_fs():
    """ This tests basic API functionality of locating a coffee place in NY
    """
    url = 'https://api.foursquare.com/v2/venues/explore'

    params = dict(
      client_id=CLIENT_ID,
      client_secret=CLIENT_SECRET,
      v='20180323',
      ll='40.7243,-74.0018',
      query='coffee',
      limit=1
    )

    resp = requests.get(url=url, params=params)
    data = json.loads(resp.text)
    meta = data['meta']
    response = data['response']

    venues =[]
    items = []
    for item in data['response']['groups']:
        info = {}
        info['items'] = item['items']
        items.append(info)

    for item in items:
            venues.append(item['items'][0]['venue'])

    return render_template('test_fs.html', meta=meta, response=response, items=items, venues=venues)

# Begin OAuth2 process with Foursquare API for user authentication
@app.route('/auth')
def auth():
    """
    Redirect the user/resource owner to the OAuth2 provider (e.g., Foursquare)
    using an URL with a few key OAuth parameters.
    """
    fs = OAuth2Session(CLIENT_ID, redirect_uri=REDIRECT_URI)
    authorization_url, state = fs.authorization_url(AUTHORIZATION_BASE_URL)
    return redirect(authorization_url)

@app.route('/callback', methods=["GET"])
def callback():
    """
    The user has been redirected back from the provider to your registered
    callback URL. With this redirection comes an authorization code included
    in the redirect URL. We will use that to obtain an access token.
    """
    fs = OAuth2Session(CLIENT_ID, redirect_uri=REDIRECT_URI)
    token = fs.fetch_token(TOKEN_URL, client_secret=CLIENT_SECRET,
                               authorization_response=request.url)

    # Save token, and redirect to the profile page
    session['oauth_token'] = token
    return redirect(url_for('.profile'))

@app.route("/profile", methods=["GET"])
def profile():
    """Fetching a protected resource using an OAuth 2 token.
    """
    token = session['oauth_token']
    # Let's fetch the checkin information of the authenticated user
    url = 'https://api.foursquare.com/v2/users/self/checkins'
    params = dict(
       oauth_token=token.get('access_token'),
       v=CURRENT_DATE
    )

    data = []
    resp = requests.get(url=url, params=params)
    data.append(resp.json())
    #print("[ PROFILE : ]", data[0]['meta']['code'])
    # max api limit is 250 per query, so continue query until reach the end
    offset = 0
    all_data = []
    while True:
        print(offset, end=' ')
        params = dict(
           oauth_token=token.get('access_token'),
           limit=250,
           sort='newestfirst',
           v=CURRENT_DATE,
           offset=offset
        )

        resp = requests.get(url=url, params=params)
        if len(resp.json()['response']['checkins']['items']) == 0:
            break #whenever api returns no rows, offset value has exceeded total records so we're done
        all_data.append(resp.json())
        offset += 250

    # Store each venue location as a row with the location_components included
    location_components = ['city', 'state', 'country', 'lat', 'lng']
    formatted_data = []
    for response in all_data:
        for item in response['response']['checkins']['items']:
            try:
                checkin = {}
                checkin['venue_name'] = item['venue']['name']
                checkin['created_at'] = item['createdAt']

                if len(item['venue']['categories']) > 0:
                    checkin['category'] = item['venue']['categories'][0]['name']

                for component in location_components:
                    if component in item['venue']['location']:
                        checkin[component] = item['venue']['location'][component]
                    else:
                        checkin[component] = np.nan
                formatted_data.append(checkin)
            except:
                pass

    df_full = pd.DataFrame(formatted_data)
    # convert unix timestamp to date and time, then drop the timestamp column
    df_full['datetime'] = df_full['created_at'].map(lambda x: dt.fromtimestamp(x).strftime('%Y-%m-%d %H:%M'))
    df_full = df_full.drop('created_at', axis=1)

    # rename lng column to lon
    df_full = df_full.rename(columns={'lng':'lon'})

    # save the entire raw downloaded check-ins data set as json
    full_path = os.path.join(PATH, FILENAME)
    with open(full_path, 'w') as f:
        f.write(json.dumps(all_data, indent=2))
    # save the entire raw downloaded check-ins data set as csv
    full_path_csv = os.path.join(PATH, FILENAME_CSV)
    df_full.to_csv(full_path_csv)

    return render_template("profile.html", filename=FILENAME, filename_csv=FILENAME_CSV, server_response = data[0]['meta']['code'], df = df_full.to_html(max_rows=6, classes='table', border=0))

@app.route("/charts")
def chart():
    """ Parse through FILENAME_CSV to create charts
    """

    full_path_csv = os.path.join(PATH, FILENAME_CSV)
    df = pd.read_csv(full_path_csv, index_col=[0], parse_dates=['datetime'])
    df['month_year'] = df.datetime.dt.to_period('M')
    df['day_of_week'] = df.datetime.dt.weekday_name

    # Line chart with total checkin count over time
    yearmonth_count = df.groupby(df.month_year.tolist(), as_index=False).size()
    yearmonth_label = yearmonth_count.index.tolist()

    cats = [ 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    day_of_week = df.groupby(df.day_of_week).size().reindex(cats)
    ## DataFrame.transform introduced in pandas 0.20.0
    ## pythonanywhere includes older version. Must do pip3 install --upgrade --user pandas
    day_of_week_prop = day_of_week.transform(lambda x: round(100 * x/x.sum(),2))
    day_of_week_label = day_of_week.index.tolist()

    # lat/long coordinates for heatmap looking only at most popular city
    # need to save as .geojson format
    def df_to_geojson(df, properties, lat='latitude', lon='longitude'):
        geojson = {'type':'FeatureCollection', 'features':[]}
        for _, row in df.iterrows():
            feature = {'type':'Feature',
                       'properties':{},
                       'geometry':{'type':'Point',
                                   'coordinates':[]}}
            feature['geometry']['coordinates'] = [row[lon],row[lat]]
            for prop in properties:
                feature['properties'][prop] = row[prop]
            geojson['features'].append(feature)
        return geojson

    top_city = df.groupby(df.city).size().sort_values(ascending=False).index.tolist()[0]
    df_top_city = df.loc[df['city'] == top_city].reset_index(drop=True)
    sample_lat = df_top_city['lat'][0]
    sample_lon = df_top_city['lon'][0]
    cols = ['venue_name', 'datetime']
    geojson = df_to_geojson(df, cols, lat='lat', lon='lon')

    full_path = os.path.join(PATH, FILENAME_GEOJSON)
    with open(full_path, 'w') as f:
        f.write(json.dumps(geojson, indent=2, default=str) )

    # bar chart for total top venues
    top_venues = df.groupby(df.venue_name).size().sort_values(ascending=False)[0:10]
    top_venues_label = top_venues.index.tolist()

    # chart for for top categories
    top_categories = df.groupby(df.category).size().sort_values(ascending=False)[0:10]
    top_categories_label = top_categories.index.tolist()

    # bar chart for top venues in past three months
    today = dt.today()
    s = '-'
    year_month = (str(today.year), str(today.month-3))
    three_months_ago = (s.join(year_month))
    mask_past_three_months = (df['datetime'] > three_months_ago)
    df_three_months = df.loc[mask_past_three_months]
    top_venues_3mo = df_three_months.groupby(df_three_months.venue_name).size().sort_values(ascending=False)[0:10]
    top_venues_3mo_label = top_venues_3mo.index.tolist()
    print(top_venues_3mo)

    # chart for top categories in past three months
    top_categories_3mo = df_three_months.groupby(df_three_months.category).size().sort_values(ascending=False)[0:10]
    top_categories_3mo_label = top_categories_3mo.index.tolist()

    return render_template('charts.html', title='Your Foursquare Swarm Check-in Summary',\
            MAPBOX_ACCESSTOKEN=MAPBOX_ACCESSTOKEN,\
            yearmonth_label=yearmonth_label, yearmonth_count=yearmonth_count,\
            filename_geojson=FILENAME_GEOJSON, mapbox_center_lat=sample_lat, mapbox_center_lon=sample_lon,\
            top_venues_label=top_venues_label, top_venues=top_venues,\
            top_categories_label=top_categories_label, top_categories=top_categories,\
            top_venues_3mo_label=top_venues_3mo_label, top_venues_3mo=top_venues_3mo,\
            top_categories_3mo_label=top_categories_3mo_label, top_categories_3mo=top_categories_3mo,\
            day_of_week_label=day_of_week_label, day_of_week=day_of_week, day_of_week_prop=day_of_week_prop)

if __name__ == "__main__":
    app.run(debug=DEBUG)
