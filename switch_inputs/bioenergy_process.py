"""
    Code to include bioenergy to generation projects info
"""
import os
import sys
import json
import random
import pandas as pd

random.seed(3)

data_path = '../data/interim/'
filename = 'bioenergy_low.csv'
clean_path = '../data/clean/bioenergy/'

plant_type = {
 'residuos_urbanos': 'natural_gas',
 'residuos_industriales': 'natural_gas',
 'digestion_anaerobia': 'natural_gas'
 'residuos_forestales': 'thermal'
}

with open(os.path.join(data_path, 'trans-regions.json'), 'r') as fp:
    trans_regions = json.load(fp)

df = pd.read_csv(os.path.join(data_path, filename), index_col=0)
df['trans_regions'] = df['lz'].astype(int).map('{0:02}'.format).map(trans_regions)
grouped = df.groupby([ 'trans_regions', 'type'])
df_sampled = pd.concat([d.loc[random.sample(list(d.index), 1)] for _, d in
                grouped]).reset_index(drop=True)
df_sampled['gen_energy_source'] = df_sampled['type'].map(plant_type)
df_sampled.rename(columns={'type':'fuel_type'}, inplace=True)
df_sampled['technology'] = 'Bioenergy'
df_sampled.to_csv(os.path.join(clean_path, './bioenergy.csv'), index=False)
#  df_sampled = pd.concat([d.loc[random.sample(d.index, 1)] for _, d in grouped]).reset_index(drop=True)
