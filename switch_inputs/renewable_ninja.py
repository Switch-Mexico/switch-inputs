""" Get wind generation profiles using Renewable Ninja API

This files gets the info. about simulations of the hourly power output from
wind plants located in a specific area.  It uses the Renewable.ninja API. 
To make use of this file, you can run the following in your console:
    pipenv run python renewable_ninja.py

   ~: python winddataninja.py <Path to CSV with Coordinates (lon/lat)> <Path to
   save the retrieved data> <Year> <Token for the API> <Height of the turbine>
   <Model of the turbine> <KW>

   Example:

   ~: python winddataninja.py ../Mesh.csv
   /home/benito/BECI/RenewablesNinjaData/2014/ 2014 "*Benito's Token*" 80
   "Vestas V90 2000" 1000


To get your token and info. regarding the height and model of the turbines,
refer to: https://www.renewables.ninja/

"""
import io
import os
import sys
import json
import yaml
import requests
import time
import pandas as pd
from tqdm import tqdm, trange

output_data = '../data/clean/wind/'

def session_handler(token):
    """ Send authorization token to the API

    """
    s = requests.session()
    # Send token header with each request
    s.headers = {'Authorization': 'Token ' + token}

    return (s)

def session_request(session, params, **kwargs):
    """ Request data

    """
    api_base = 'https://www.renewables.ninja/api/v1/'
    url = api_base + 'data/wind'
    if kwargs['debug']:
        print (json.dumps(params, sort_keys=True, indent=4))
    saveme = 0
    while True:
        r = session.get(url, params=params)
        saveme +=1
        if saveme == 3:
            raise Exception('API responded {0}'.format(r.reason))
        if r.status_code == 200:
            return (r)
        elif r.reason == 'Too Many Requests':
            pbar = tqdm(total=60, leave=False)
            pbar.set_description("Too Many requests. Wait 60s")
            for i in range(60):
                pbar.update(1)
                time.sleep(1)
            pbar.close()
            continue
        else:
            raise Exception('API request responded {0}. Reason: {1}'.format(r.status_code,  r.reason))

def timezone_transform(df, year, timezone='UTC', localtime=False):
    """ Convert the DatetimeIndex to selected timezone

    """
    df['time'] = pd.DatetimeIndex(df['UTC']).tz_convert('Mexico/General')
    if localtime:
        df['time'] = df['UTC'].tz_localize(None)

    # Push all the data to the same year
    # Though this only work for pushing up
    df.loc[df['time'].dt.year != year, 'time'] += pd.Timedelta(days=365)
    df.set_index('time', drop=True, inplace=True)
    df = df.sort_index()
    return (df)

def single_turbine(params, **kwargs):
    """ Single turbine requests

    """
    s = session_handler(params.pop('token'))
    r = session_request(s, params, **kwargs)
    df = pd.read_csv(io.StringIO(r.text), skiprows=1)
    df['UTC'] = pd.DatetimeIndex(pd.to_datetime(df['UTC'])).tz_localize('utc')
    return (df)

def multiple_turbines(data, params, **kwargs):
    """ Multiple turbine requests


    Todo:
        * Create function that verify existance of output folders

    """
    s = session_handler(params.pop('token'))
    ixs = data.index
    pbar = tqdm(ixs)
    for ix in pbar:
        filename = data.loc[ix]['filename']
        pbar.set_description("Downloading file {0}".format(filename))
        pbar.refresh() # to show immediately the updat
        if ix % 6 == 0 and ix != 0:
            time.sleep(60)
        params['lat'] = data.loc[ix]['lat']
        params['lon'] = data.loc[ix]['lng']
        r = session_request(s, params, **kwargs)
        df = pd.read_csv(io.StringIO(r.text), skiprows=1)
        df['UTC'] = pd.DatetimeIndex(pd.to_datetime(df['UTC'])).tz_localize('utc')
        df['cf'] = df['kW']/params['capcaity']
        output = timezone_transform(df, 2016)
        output.to_csv(os.path.join(output_data, filename))
    return (True)


if __name__ == '__main__':
    with open("secrets.yml", 'r') as stream:
        try:
            #  print(yaml.load(stream))
            config_files = yaml.load(stream)
        except yaml.YAMLError as exc:
            print('Token not found. Please check you put your API_KEY')
            raise exc
    args = {
        'date_from': '2016-01-01',
        'date_to': '2016-12-31',
        'capacity': 2000,
        'height': 100,
        'turbine': 'Vestas V80 2000',
        'format': 'csv',
        'metadata': True,
        'token':  config_files['API_KEY']
    }
    if sys.argv[1] == 'single':
        args['lat'] = sys.argv[2], #34.125,
        args['lon'] = sys.argv[3], #-99.814,
        df = single_turbine(args, debug=True)
        df = timezone_transform(df, 2016, 'Mexico/General')
        print (df.head())
    elif sys.argv[1] == 'multiple':
        data_path = '../data/interim/'
        df = pd.read_csv(os.path.join(data_path, 'wind_cluster_centroids.csv'))
        multiple_turbines(df, args, debug=False)
