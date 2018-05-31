"""
    Clean bioenergy data from AZEL
"""
import os
import json
import itertools
import geopandas as gpd
import pandas as pd

os.makedirs('data', exist_ok=True)

projection = 'epsg:4326'
name = ['pecuarios', 'forestales', 'industriales', 'urbanos']
scenario = ['E3', 'E1']

for scenario, name in itertools.product(scenario, name):
    # Load bioenergy shape file
    print ('Reading file: {}_R{}.shp'.format(scenario, name))
    df = gpd.read_file('../data/interim/shapes/FBio_{0}_R{1}.shp'.format(scenario,
                                                                        name))
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

    if not 'forestal' in name:
        join = gpd.sjoin(df, lz, op='within')
    else:
        join = gpd.overlay(lz, df, how='intersection')

    # Get specific columns for output data
    try:
        columns = ['trans-region', 'X', 'Y', 'CLASIFICAC', 'TIPO', 'PROCESO',
                   'GENE_GWha', 'CAPINST_MW', 'FP']
        bio = join[columns].copy();
    except KeyError:
        columns = ['trans-region', 'CLASIFICAC', 'TIPO', 'PROCESO',
                   'GENE_GWha', 'CAPINST_MW', 'FP']
        bio = join[columns].copy();
    bio['CLASIFICAC'] = bio.CLASIFICAC.map(str.lower).str.replace(' ', '_')
    bio['TIPO'] = bio.TIPO.map(str.lower).str.replace(' ', '_')
    bio['PROCESO'] = bio.PROCESO.map(str.lower).str.replace(' ', '_')
    if 'E3' in scenario:
        scenario = 'high'
    else:
        scenario = 'low'
    bio.loc[:, 'scenario'] = scenario
    bio.loc[:, 'id'] = name
    bio = bio.rename(columns={'X': 'lng', 'Y': 'lat', 'CLASIFICAC': 'source',
                             'TIPO': 'category', 'FP': 'cf',
                             'GENE_GWha': 'gen_GWha', 'CAPINST_MW':'cap_MW',
                             'PROCESO': 'fuel_type'})
    print ('Saving data: {0}_{1}'.format(scenario, name))
    bio.to_csv('data/bioenergy_{0}_{1}.csv'.format(scenario, name), index=False)
