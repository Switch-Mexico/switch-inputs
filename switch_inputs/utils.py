"""
    Utilities por switch data creation
"""
import os
import sys
import yaml
import glob
import logging
import click
import pandas as pd
import requests
import math
from tqdm import tqdm
from logging.config import fileConfig
from context import *
from pathlib import Path
from time import sleep



#  logfile_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'log.ini')
#  #  print ( f'Log file configuration located at: {logfile_path}')
#  fileConfig(logfile_path)
#  logger = logging.getLogger('Logger')

@click.group(invoke_without_command=True)
@click.option('--verbose', default=False)
@click.pass_context
def init(ctx, verbose):
    """ Initialize switch inputs datasets"""
    click.secho('Starging app!', fg='green')
    #  ctx.obj['verbose'] = verbose
    ctx.invoke(init_dirs)
    ctx.invoke(get_data)
    click.secho('Sucess. App ended correctly ✓\n', fg='green')
    pass

@init.command()
@click.pass_context
def init_dirs(ctx):
    """ This function should init the environment"""

    default_dir = 'data/default'
    output_dir = 'data/switch_inputs'
    click.secho('Creating folder: %s' %
            click.format_filename(f'{default_dir}'),
            fg='yellow')
    Path(default_dir).mkdir(parents=True, exist_ok=True)
    click.secho('Creating folder: %s' %
            click.format_filename(f'{output_dir}'),
            fg='yellow')
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    click.secho('Creation sucessfull ✓\n', fg='green')


@init.command('get_data')
@click.pass_context
def get_data(ctx):
    """ Download default data from Gdrive"""
    data = {
        "periods.yaml": "1MD93eDd9W4GWaTAhngUxswsBRLcpPksQ",
        "capacity_limit.csv": "1RJHOMnpQGp3dpVhTEuyTuBM2XeLQ1256",
        "gen_build_predetermined.tab": "1Wdy7G-RsFPzl1dEy3SgLSd5MB-3B-Er0",
        "rps_targets.yaml": "18x5zV5gqv_PYMEg5jrNJe7y6xde8pPve",
        "generation_projects_info.tab": "1i_atr5nCMTxkDvhBc1MmVVvcpPCPh3FN",
        "gen_build_costs.tab": "193QPGYYkJrF1ZYSI5Va0_T2pJjjzAKS9",
        "restriction.yaml": "1qP0bs6c2Bn4o0NgWJX-uPRSKG57aPNk4",
        "periods_big.yaml": "1O2hEeFzhtDSfPMuCRjGbeuDWoFYIGnVM",
        "technology_cost.csv": "1qEs16DUTr2SVk-Ujq-7OhPWbV3zZjD0H",
        "load_zones.csv": "1TJwzDsZkbhXTghrGp4Vwr8vN2BaQb_1y",
        "gen_cost_reference.csv": "1F14HcLnYskejFS9B6j6lJXTHJ6eLTdcX",
        "cost_tables.csv": "1FmPECjnlYOJ0YuvwibRibL7K6F978NCC",
        "HighLoads.csv": "19-ZfjD6aU21ZY6dshOPZsOpSQp8e9Rc5",
        "fuel_cost.csv": '11h3WcwmvC1SUHgW5YHIvWdWMbFiamwTA',
        "renewable.csv": "1lP3l7hthr2b8imZOOku1FO7DaKOg5xio"
        }

    def download_file_from_google_drive(id, destination):
        URL = "https://docs.google.com/uc?export=download"
        #  URL = "https://www.googleapis.com/drive/v3/files"

        session = requests.Session()

        response = session.get(URL, params = { 'id' : id }, stream = True)
        token = get_confirm_token(response)

        if token:
            params = { 'id' : id, 'confirm' : token }
            response = session.get(URL, params = params, stream = True)

        save_response_content(response, destination)

    def get_confirm_token(response):
        for key, value in response.cookies.items():
            if key.startswith('download_warning'):
                return value

        return None

    def save_response_content(response, destination):
        CHUNK_SIZE = 32*1024
        #  total_size = int(response.headers.get('Content-Length', 0));
        total_size = int(response.headers.get('Content-Length', 0))

        filename = os.path.basename(destination)

        #FIXME: Temporal fix due to google drive api.
        # It does no return the Content-Length for heavier files.
        if filename == 'HighLoads.csv':
            total_size = 84516710
        elif filename == "renewable.csv":
            total_size = 180786774
        else:
            pass

        click.secho(f'Downloading: {filename}', fg='cyan')
        with open(destination, "wb") as f:
            with tqdm(
                    total=total_size,
                    unit='B',
                    unit_scale=True,
                    unit_divisor=1024,
                    ) as pbar:
                for chunk in response.iter_content(CHUNK_SIZE):
                    if chunk:
                        pbar.update(len(chunk))
                        f.write(chunk)

    click.secho('Downloading data...\n', fg='blue')

    for key, value in data.items():
        destination, file_id = key, value
        destination = os.path.join(default_path, destination)
        download_file_from_google_drive(file_id, destination)

def look_for_file(filename, path):
    file_path = os.path.join(path, filename)
    match = [pattern for pattern in glob.glob(f'{file_path}.*')]
    if not match:
        return False

    if len(match) < 2:
        return os.path.splitext(match[0])
    elif len(match) > 2:
        click.echo(f'Multiple files detected for {filename}. Please delate one')
        sys.exit(1)
        return False


def read_yaml(path, filename: str):
    """ Read yaml file"""

    file_path = os.path.join(path, filename)

    with open(file_path, 'r') as stream:
        try:
            yaml_file = yaml.load(stream, Loader=yaml.FullLoader)
        except yaml.YAMLError as exc:
            raise (exc)

    return yaml_file


def create_gen_build_cost_new(df_gen, ext='.tab', path=default_path,
    **kwargs):
    """ Create gen build cost output file

    Args:
        data (pd.DataFrame): dataframe witht dates,
        ext (str): output extension to save the file.

    Note(s):
        * .tab extension is to match the switch inputs,
    """
    cost_table = pd.read_csv(os.path.join(path, 'gen_cost_reference.csv'))
    tech_costs = pd.read_csv(os.path.join(path, 'technology_cost.csv'))

    if ext == '.tab': sep='\t'

    output_file = output_path + 'gen_build_costs' + ext

    # TODO:  Change the direction of this file

    periods = read_yaml(path, 'periods.yaml')

    # FIXME: This will only work if there is no repeated elements

    gen_costs = pd.merge(df_gen, cost_table, on='gen_tech')
    column_order = ['GENERATION_PROJECT', 'build_year', 'gen_overnight_cost',
            'gen_fixed_om', 'gen_tech']

    output_list = []
    #  output_list.append(gen_costs[cols])
    for period in periods['INVESTMENT_PERIOD']:
        #  print (period)
        gen_costs.loc[:, 'build_year'] = period
        output_list.append(gen_costs[column_order])

    gen_build_cost = pd.concat(output_list)
    gen_build_cost = modify_costs(gen_build_cost)
    #  gen_build_cost.to_csv('gen_build_cost.tab', sep=sep)

    return (gen_build_cost)

def modify_costs(data, ext='.tab', path=default_path):
    """ Modify cost data to derate it

    Args:
        data (pd.DataFrame): dataframe witht dates,

    Note(s):
        * This read the cost table and modify the cost by period
    """
    if ext == '.tab': sep='\t'

    output_file = 'gen_build_cost' + ext

    # TODO: Make a more cleaner way to load the file
    cost_table = pd.read_csv(os.path.join(path, 'cost_tables.csv'))

    df = data.copy()

    techo = cost_table['technology'].unique()
    for index in df.build_year.unique():
        mask = (df['gen_tech'].isin(techo)) & (df['build_year'] == index)
        for tech in df['gen_tech'].unique():
            if tech in cost_table['technology'].unique():
                mask2 = (cost_table['technology'] == tech) & (cost_table['year'] == index)
                cost_table.loc[mask2, 'gen_overnight_cost'].values[0]
                df.loc[mask & (df['gen_tech'] == tech), 'gen_overnight_cost'] = cost_table.loc[mask2, 'gen_overnight_cost'].values[0]
                df.loc[mask & (df['gen_tech'] == tech), 'gen_fixed_om'] = cost_table.loc[mask2, 'gen_fixed_om'].values[0]

    df = df.sort_values(['GENERATION_PROJECT', 'build_year'],
                        ascending=[True, True])

    # TODO: Change direction of the output_file
    # Save file
    #  df.to_csv(output_file, sep=sep, index=False)

    return (df)

def init_scenario():
    """  Create default scenario with existing technology for each loadzone """

    df_gen = pd.read_csv(os.path.join(default_path,
        'generation_projects_info.tab'), sep='\t')
    column_order = df_gen.columns

    #FIXME: Quick fix to replace tg for turbo_gas
    df_gen['gen_tech'] = df_gen['gen_tech'].replace('tg', 'turbo_gas')

    gen_default = pd.read_csv(os.path.join(default_path,
                                            'technology_cost.csv'))

    #TODO: This should be a dictionary. Maybe YAML
    load_zones = pd.read_csv(os.path.join(default_path, 'load_zones.csv')
                             , sep='\t', usecols=[0])

    # Restriction
    restriction = read_yaml(default_path, 'restriction.yaml')

    # Get technologies that are not in a load zone
    gen_restriction = {key:
            list(set(df_gen['gen_tech']) - set(df_gen.loc[df_gen['gen_load_zone'] == key, 'gen_tech']))
                        for key in load_zones['LOAD_ZONES']}

    # Quick fix to include solar, wind and geothermal for all loadzones
    for k in gen_restriction:
        gen_restriction[k] = [val for val in gen_restriction[k] if val not in
                ('wind', 'solarpv', 'geothermal')]
    iterator = 1
    prop_gens = []
    for row in load_zones.itertuples():
        lz = row[1]
        gen_lz_restriction = gen_restriction[lz]

        # Get restriction technology by load zone
        lz_restriction = [key for key, value in restriction['technology'].items()
                                                if lz in value]

        # Combine load_zone manual restriction and legacy restriction
        tech_rest = set(gen_lz_restriction) | set(lz_restriction)

        # Filter restricted technologiesj
        prop_gen = gen_default.loc[~gen_default['gen_tech'].isin(tech_rest)].copy()

        # Include load zone information
        prop_gen.loc[:, 'gen_load_zone'] = lz

        # Rename generation project
        prop_gen.loc[:, 'GENERATION_PROJECT'] = (prop_gen['GENERATION_PROJECT']
                                                    .map(str.lower)
                                                    + f'_{iterator:03d}')
        prop_gens.append(prop_gen)

        iterator +=1
    df_gen = pd.concat(prop_gens)

    cap_limit = pd.read_csv(os.path.join(default_path, 'capacity_limit.csv'))
    for index, row in cap_limit.iterrows():
        df_gen.loc[df_gen['GENERATION_PROJECT'] == row['project'],
                'gen_capacity_limit_mw'] = row['capacity_limit']
    #  df_gen[column_order].to_csv('generation_test.tab', sep='\t', index=False)

    return df_gen[column_order]


if __name__ == '__main__':
    #  pp = PowerPlant('UUUID', 'solar', 'solar', 'Mulege')
    #  pp.add()
    init_scenario()
    #  gen_build_cost = create_gen_build_cost_new()
    #  modify_costs(gen_build_cost)
