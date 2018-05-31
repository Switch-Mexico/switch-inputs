"""
    Clean geoenergy data from AZEL
"""
import os
import json
import itertools
import geopandas as gpd
import pandas as pd

os.makedirs('data', exist_ok=True)

projection = 'epsg:4326'
scenario = ['Esc3', 'Esc1']

for scenario in scenario:
    # Load geoenergy shape file
    print ('Reading file: {}_R.shp'.format(scenario))
    df = gpd.read_file('../data/interim/shapes/AP_Geotermica_{}.shp'.format(scenario))
    df = df[df.geometry.notnull()].to_crs({'init': projection})

    # Load transmission region dictionary
    with open(os.path.join('../data/interim/', 'trans-regions.json'), 'r') as fp:
        trans_regions = json.load(fp)

    # Load transmission region shapefiles
    lz = gpd.read_file('../data/interim/shapes/Mask_T.shp')
    lz = lz.to_crs({'init': projection})
    lz.loc[:, 'trans-region'] = (lz['ID'].astype(int)
                                         .map('{0:02}'.format)
                                         .map(trans_regions))
    assert lz.crs == df.crs

    join = gpd.sjoin(df, lz, op='within')

    # Get specific columns for output data
    columns = ['trans-region', 'LONGITUD', 'LATITUD', 'TEMP', 'ENER_MED',
                'CAP_MED']
    geo = join[columns].copy();

    if 'Esc3' in scenario:
        scenario = 'high'
    else:
        scenario = 'low'
    geo.loc[:, 'scenario'] = scenario
    geo = geo.rename(columns={'LATITUD': 'lng', 'LONGITUD': 'lat',
                             'TEMP': 'temperature', 'ENER_MED': 'gen_MWh',
                             'CAP_MED': 'cap_MW'})
    print ('Saving data: {0}_geothermal'.format(scenario))
    geo.to_csv('data/{0}_geothermal.csv'.format(scenario), index=False)
