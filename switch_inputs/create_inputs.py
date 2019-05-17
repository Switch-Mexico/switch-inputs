"""
Code to automatically generate inputs for switch.

Developers:
    Pedro Andres Sanchez Perez
    Sergio Castellanos Rodriguez
    And other I do not know.
"""
import os
import sys
import yaml
import numpy as np
import pandas as pd
from context import *
from collections import OrderedDict
from utils import read_yaml, init_scenario
from utils import create_gen_build_cost_new, look_for_file


def get_load_data(path=default_path, filename='HighLoads.csv',
         total=False, *args, **kwargs):
    """ Read load consumption data

    Args:
        path (str): path to the file,
        filename (str): name of the file,
        total (bool): if true returns only the sum of all loads.

        TODO:
            * Migrate this function to utilities
            * This could be a csv or it could connect to a DB.
            * This could be a csv or it could connect to a DB.
    """
    if filename == 'high':
        filename = 'HighLoads.csv'
    elif filename == 'low':
        filename = 'LowLoads.csv'
    elif filename == 'medium':
        filename = 'MediumLoads.csv'
    else:
        # Is this really necessary?
        sys.exit(1)


    file_path = os.path.join(path, filename)

    try:
        df = pd.read_csv(file_path)
    except FileNotFoundError:
        # TODO: Change this to f' string format
        raise FileNotFoundError('File not found. Please verify the file is in: {}'.format(os.path.join(path, filename)))

    # Calculate the sum of loads
    df['total'] = df.sum(axis=1)

    try:
        # Shift load data to match generation.
        df.loc[:, 'hour'] -= 1
    except:
        print ('Something went wrong')
        pass

    # Add datetime index
    df.index = pd.to_datetime(df[['year', 'month', 'day', 'hour']])
    df.index.rename('datetime', inplace=True)

    # Remove  columns
    df = df.drop(['year', 'month', 'day', 'hour'], axis=1)

    df = df.sort_index()

    if total:
        return df[['total']]
    else:
        return df

def get_peak_day(data, number, freq='MS'):
    """ Construct a representative day based on a single timestamp

    Args:
        data (pd.DataFrame): data to filter,
        number (float): number of days to return.

    Note:
        * Month start is to avoid getting more timepoints in a even division
    """
    years = []

    # Check if number of timepoints is multiple
    if not 24 % number == 0 :
        raise ValueError('Odd number of timepoints. Use even number')

    # Iterate over all months
    for _, group in data.groupby([pd.Grouper(freq='A'),\
        pd.Grouper(freq=freq)]):

        delta_t = int(24/number)

        #Temporal fix for duplicates
        group = group[~group.index.duplicated(keep='last')]

        # Get index of max value
        peak_timestamp = group.idxmax()

        # Convert the max value index to timestamp
        mask = peak_timestamp.strftime('%Y-%m-%d')

        peak_loc = group[mask].index.get_loc(peak_timestamp)

        # Check if delta_t does not jump to next day
        if (peak_timestamp.hour + delta_t ) > 23:
            peak_timestamps = group.loc[mask].iloc[peak_loc::-delta_t]
            if len(peak_timestamps) < delta_t:
                missing = number - len(peak_timestamps)
                peak_timestamps = (peak_timestamps.append(group
                                    .loc[mask]
                                    .iloc[peak_loc::delta_t][1:missing+1]))
        else:
            peak_timestamps = group.loc[mask].iloc[peak_loc::delta_t]
            if len(peak_timestamps) < delta_t:
                missing = number - len(peak_timestamps)
                peak_timestamps = (peak_timestamps.append(group
                                    .loc[mask]
                                    .iloc[peak_loc::-delta_t][1:missing+1]))

        # Sort the index. Why not?
        peak_timestamps = peak_timestamps.sort_index().reset_index()

        years.append(peak_timestamps)

    output_data = pd.concat(years, sort=True)
    output_data = output_data.rename(columns={'datetime':'date',
                                    'total':'peak_day'})
    return (output_data)

def get_median_day(data, number, freq='MS'):
    """ Calculate median day giving a timeseries

    Args:
        data (pd.DataFrame): data to filter,
        number (float): number of days to return.

    Note(s):
        * Month start is to avoid getting more timepoints in a even division
    """

    years = []

    for _, group in data.groupby([pd.Grouper(freq='A'),\
        pd.Grouper(freq=freq)]):
        # Calculate the daily mean
        grouper = group.groupby(pd.Grouper(freq='D')).mean()
        if len(grouper) & 1:
            # Odd number of days
            index_median = grouper.loc[grouper==grouper.median()].index[0]
        else:
            # Even number of days
            index_median = (np.abs(grouper-grouper.median())).idxmin()
        years.append(group.loc[index_median.strftime('%Y-%m-%d')].iloc[::int((24/number))].reset_index())
    output_data = pd.concat(years, sort=True)
    output_data.rename(columns={'datetime': 'date', 'total':'median_day'},\
            inplace=True)

    return (output_data)

def create_investment_period(path=default_path, ext='.tab', **kwargs):
    """ Create periods file using periods.yaml input

    Args:
        path (str): path to file,
        ext (str): output extension to save the file

    Note(s):
        * .tab extension is to match the switch inputs,
    """

    output_file = output_path + 'periods' + ext

    periods = read_yaml(path, 'periods.yaml')

    d = OrderedDict(periods)
    periods_tab = pd.DataFrame(d)
    periods_tab = periods_tab.set_index('INVESTMENT_PERIOD')
    periods_tab.to_csv(output_file, sep='\t')


def create_rps(path=default_path, filename='rps_targets',
                output_name='rps_targets', ext='.yaml', output_ext='.tab'):
    """ Create rps targets file using rps_target.yaml"""

    if output_ext == '.tab': sep='\t'

    output_file = output_path + output_name + output_ext
    file_path = os.path.join(path, filename + ext)

    if ext == '.yaml':
        rps = read_yaml(path, 'rps_targets.yaml')

    d = OrderedDict(rps)
    rps_tab = pd.DataFrame(d)
    rps_tab = rps_tab.set_index('PERIOD')

    rps_tab.to_csv(output_file, sep=sep)



def create_timepoints(data, ext='.tab', **kwargs):
    """ Create timepoints file

    This function create the timepoints for all the peak and median days
    selected from the load profile. The output is sorted by date.

    Args:
        data (pd.DataFrame): dataframe witht dates ,
        ext (str): output extension to save the file.

    Note(s):
        * .tab extension is to match the switch inputs,
    """

    # Filename convention
    if ext == '.tab': sep='\t'

    output_file = output_path + 'timepoints' + ext

    # If multiple timeseries included in data
    if isinstance(data, list):
        data = pd.concat(data, sort=True)

    # Sort timepoints by date
    data.sort_values('date', inplace=True)

    # TODO: Write test to check if columns exist
    data = data[['timestamp', 'TIMESERIES', 'daysinmonth']]
    data.index.name = 'timepoint_id'
    data = data.reset_index(drop=True)
    data = data.rename(columns={'TIMESERIES':'timeseries'})
    data.index += 1  # To start on 1 instead of 0
    data.index.name = 'timepoint_id'
    output_cols = ['timestamp', 'timeseries']
    data[output_cols].to_csv(output_file, sep=sep)


def create_strings(data, scale_to_period, identifier='P',  ext='.tab',
        **kwargs):
    """ Create strings to process files

    Args:
        data (pd.DataFrame): dataframe witht dates,
        scale_to_period (int): difference between period ranges,
        identifier (str): identifier for each series
        ext (str): output extension to save the file.

    Note(s):
        * .tab extension is to match the switch inputs,
    """

    strftime = '%Y%m%d%H' #  Strftime for label
    data['timestamp'] = data['date'].dt.strftime(strftime)
    data['TIMESERIES'] = data['date'].dt.strftime('%Y_%m{}'.format(identifier))
    data['daysinmonth'] = data['date'].dt.daysinmonth

    # TODO: Fix this. Probably bug in near future
    data['ts_period'] = data['date'].dt.year
    data['scale_to_period'] = scale_to_period

    return (data)

def create_timeseries(data, number, ext='.tab', **kwargs):
    """ Create timeseries output file

    Args:
        data (pd.DataFrame): dataframe witht dates,
        number (int) : number of timepoints
        ext (str): output extension to save the file.

    Note(s):
        * .tab extension is to match the switch inputs,
    """

    # Filename convention
    output_file = output_path + 'timeseries' + ext
    if ext == '.tab': sep='\t'

    # If multiple timeseries included in data
    if isinstance(data, list):
        data = pd.concat(data, sort=True)

    # Sort values by date
    data.sort_values('date', inplace=True)
    # Extract unique timeseries_id
    timeseries = data[['TIMESERIES', 'daysinmonth', 'ts_period',
        'scale_to_period']].drop_duplicates('TIMESERIES')
    timeseries = timeseries.reset_index(drop=True)

    timeseries['ts_duration_of_tp'] = 24/number
    timeseries['count'] = timeseries.groupby('ts_period')['TIMESERIES'].transform(len)
    timeseries['ts_num_tps'] = data[['timestamp', 'TIMESERIES']].groupby('TIMESERIES').count().values

    def scaling(data):
        """ Scale based on median or peak day """

        # Scaling for peak day
        peak_days = data['TIMESERIES'].str.endswith('P')
        median_days = data['TIMESERIES'].str.endswith('M')

        data.loc[peak_days, 'ts_scale_to_period'] = data['scale_to_period']
        data.loc[median_days, 'ts_scale_to_period'] = (
            (data['scale_to_period'] * 24 *
                    (data['daysinmonth'] - 1))
                    /
            (data['ts_duration_of_tp'] * data['ts_num_tps'])
            )
        data['weight'] = data['ts_duration_of_tp'] * data['ts_num_tps'] * \
        data['ts_scale_to_period']
        return (data)

    timeseries = scaling(timeseries)

    #  timeseries.index += 1  # To start on 1 instead of 0
    timeseries.index.name = 'timepoint_id'


    # Delete unused columns
    del timeseries['daysinmonth']
    del timeseries['scale_to_period']
    del timeseries['count']
    del timeseries['weight']

    timeseries.to_csv(output_file, index=False, sep=sep)

def create_variablecp(gen_project, data, timeseries_dict, path=default_path, ext='.tab', **kwargs):
    """ Create variable capacity factor  output file

    Args:
        data (pd.DataFrame): dataframe witht dates,
        timeseries_dict (Dict): dictionary with the timeseries for each period,
        path (string): path to renewable energy file,
        ext (str): output extension to save the file.

    Note(s):
        * .tab extension is to match the switch inputs,
    """

    # Filename convention
    output_file = output_path + 'variable_capacity_factors' + ext
    if ext == '.tab': sep='\t'

    # If multiple timeseries included in data
    if isinstance(data, list):
        data = pd.concat(data, sort=True)

    # Check if file exist and removeit
    if os.path.exists(output_file):
        os.remove(output_file)

    output_file = output_path + 'variable_capacity_factors' + ext

    file_name = 'renewable.csv'

    ren_cap_data = pd.read_csv(os.path.join(path, file_name), index_col=0,
                               parse_dates=True)
    ren_cap_data = ren_cap_data.loc[ren_cap_data['project_name'].isin(gen_project['GENERATION_PROJECT'])]

    # Quick fix to names. I need to include more code here
    replaces = [('e', 'é'), ('a', 'á'), ('i', 'í'), ('o', 'ó'), ('u', 'ú') ,
               ('n', 'ñ')]
    try:
        for tupl in replaces:
            ren_cap_data['GENERATION_PROJECT'] = ren_cap_data['GENERATION_PROJECT'].str.replace(tupl[1], tupl[0])
    except KeyError:
        pass

    # Extract datetime without year information
    filter_dates = pd.DatetimeIndex(data['date'].reset_index(drop=True)).strftime('%m-%d %H:%M:%S')

    ren_tmp = ren_cap_data.copy()
    #  print (ren_tmp.head())

    list1 = []
    for row, value in timeseries_dict.items():
        #  print (row)
        tmp2 = pd.concat(value, sort=True)
        filter_dates = (pd.DatetimeIndex(tmp2['date']
                                    .reset_index(drop=True))
                                    .strftime('%m-%d %H:%M:%S'))
        grouped = (ren_tmp[ren_tmp['time'].isin(filter_dates)]
                    .reset_index(drop=True)
                    .groupby('project_name', as_index=False))
        list1.append(pd.concat([group.reset_index(drop=True)
            for name, group in grouped], sort=True))

    variable_cap = pd.concat(list1, sort=True)
    # FIXME: Temporal fix
    try:
        del variable_cap['GENERATION_PROJECT']
    except:
        pass
    variable_tab = variable_cap.groupby('project_name')
    for keys in variable_tab.groups.keys():
        data = variable_tab.get_group(keys).reset_index(drop=True)
        data.index +=1
        data.index.name = 'timepoint'
        data.rename(columns={'capacity_factor': 'gen_max_capacity_factor',
                             'project_name':'GENERATION_PROJECT'},
                   inplace=True)
        data.reset_index()[['GENERATION_PROJECT', 'timepoint',
            'gen_max_capacity_factor']].to_csv(output_file, sep=sep,
                    index=False, mode='a', header=(not
                        os.path.exists(output_file)))

def create_loads(load, data, ext='.tab', **kwargs):
    """ Create load data output file

    Args:
        load (pd.DataFrame): load data
        data (pd.DataFrame): dataframe witht dates,
        ext (str): output extension to save the file.

    Note(s):
        * .tab extension is to match the switch inputs,
    """
    if 'total' in load.columns:
        del load['total']

    # Filename convention
    output_file = output_path + 'loads' + ext
    if ext == '.tab': sep='\t'

    # If multiple timeseries included in data
    if isinstance(data, list):
        data = pd.concat(data, sort=True)

    loads_tmp = load.copy() #[load.year <= 2025]

    # FIXME: This function is weird. We will need to change it
    # for something clearer.
    # Get data from the datetime provided

    unstack_loads = (loads_tmp.loc[data['date']] # Get filter dates
                        .reset_index(drop=True)  # Remove datetime
                        .unstack(0))             # Change rows and columns

    # Temporal fix to convert series to dataframe
    loads_tab = pd.concat([group.reset_index()
                        for _, group in unstack_loads.groupby(level=0)]
                        , sort=True)

    # Renaming columns
    loads_tab = loads_tab.rename(columns={'level_0':'LOAD_ZONE',
                                0:'zone_demand_mw',
                                'level_1': 'TIMEPOINT'})

    # Restart numbering of timepoint to start from 1
    loads_tab.loc[:, 'TIMEPOINT'] += 1

    # Change columns order
    columns_order = ['LOAD_ZONE', 'TIMEPOINT', 'zone_demand_mw']
    loads_tab = loads_tab[columns_order]

    # Save output file
    loads_tab.to_csv(output_file, sep=sep, index=False)

def create_gen_build_cost(gen_project, gen_legacy,  ext='.tab',
        path=default_path,
    **kwargs):
    """ Create gen build cost output file

    Args:
        data (pd.DataFrame): dataframe witht dates,
        ext (str): output extension to save the file.

    Note(s):
        * .tab extension is to match the switch inputs,
    """

    if ext == '.tab': sep='\t'
    output_file = output_path + 'gen_build_costs' + ext

    periods = read_yaml(path, 'periods.yaml')

    output_costs = []
    gen_legacy.rename(columns={'PROJECT': 'GENERATION_PROJECT'}, inplace=True)
    costs_legacy = pd.read_csv(os.path.join(path,'gen_build_costs.tab'), sep='\t')
    columns = ['GENERATION_PROJECT','gen_overnight_cost', 'gen_fixed_om']
    output_columns = ['GENERATION_PROJECT', 'build_year', 'gen_overnight_cost',
                        'gen_fixed_om']

    # Merge to get the build year of the predetermined plants
    merged = pd.merge(gen_legacy, costs_legacy[columns], on=['GENERATION_PROJECT'])

    # TODO: Check why we get duplicate values from the previous row
    merged.drop_duplicates('GENERATION_PROJECT', inplace=True)
    old_plants = gen_legacy['GENERATION_PROJECT'].unique()
    new_plants = gen_project.loc[~gen_project['GENERATION_PROJECT'].isin(old_plants)]

    # First add old plants 
    output_costs.append(merged[output_columns])

    # Add new plants
    new_cost = create_gen_build_cost_new(new_plants)
    output_costs.append(new_cost)

    gen_build_cost = pd.concat(output_costs, sort=True)

    # FIXME: Temporal fix to avoid duplicate entries
    df = (gen_build_cost.sort_values('gen_fixed_om')
            .drop_duplicates(subset=['GENERATION_PROJECT', 'build_year'],
                    keep='last'))
    df = df.sort_values(by=['GENERATION_PROJECT', 'build_year'])
    df[output_columns].to_csv(output_file, sep=sep, index=False)
    #  gen_build_cost.to_csv(output_file, sep=sep, index=False)

def modify_costs(data, path=default_path):
    """ Modify cost data to derate it

    Args:
        data (pd.DataFrame): dataframe witht dates,

    Note(s):
        * This read the cost table and modify the cost by period
    """

    # TODO: Make a more cleaner way to load the file
    cost_table = pd.read_csv(os.path.join(path, 'cost_tables.csv'))

    df = data.copy()
    techo = cost_table['Technology'].unique()
    for index in df.build_year.unique():
        mask = (df['gen_tech'].isin(techo)) & (df['build_year'] == index)
        df.loc[mask]
        cost_table.loc[cost_table['Year'] == index]
        for tech in df['gen_tech'].unique():
            if tech in cost_table['Technology'].unique():
                mask2 = (cost_table['Technology'] == tech) & (cost_table['Year'] == index)
                df.loc[mask & (df['gen_tech'] == tech)]
                cost_table.loc[mask2, 'gen_overnight_cost'].values[0]
                df.loc[mask & (df['gen_tech'] == tech), 'gen_overnight_cost'] = cost_table.loc[mask2, 'gen_overnight_cost'].values[0]
    return (df)

def gen_build_predetermined(existing, path=default_path, ext='.tab'):
    """ Construct gen build predetermined file"""
    output_file = output_path + 'gen_build_predetermined' + ext

    if ext == '.tab': sep = '\t'

    # FIXME: Check what format is better to read
    file_name = 'gen_build_predetermined' + ext

    file_path = os.path.join(path, file_name)

    gen_legacy = pd.read_csv(file_path, sep=sep) if existing else None

    gen_legacy.to_csv(output_file, sep=sep, index=False)

    return gen_legacy

def create_fuel_cost(path=default_path, ext='.tab'):
    """ Create fuel_costs.tab """
    output_file = output_path + 'fuel_cost' + ext
    periods = read_yaml(path, 'periods.yaml')
    fuel_costs = pd.read_csv(os.path.join(path, 'fuel_cost.csv'), index_col=0)
    fuel_cost = fuel_costs.loc[fuel_costs['period'].isin(periods['INVESTMENT_PERIOD'])]
    fuel_cost.to_csv(output_file)

if __name__ == "__main__":
    pass
