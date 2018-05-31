"""
    Code to plot results from switch
"""

import os
import sys
import errno
import pandas as pd

script_path = os.path.dirname(__file__)
parent_path = os.path.dirname(os.path.dirname(__file__))
data_path = os.path.join(parent_path, 'data/clean/loads')
output_path  = os.path.join(parent_path, 'data/clean/switch_outputs')

def get_data(path: os.PathLike=output_path, 
    filename: str='gen_cap.txt', sep: str='\t',
    **kwargs) -> pd.DataFrame:
    """
        Get data to plot
    """
    print (os.path.join(path, filename))
    file_path = os.path.join(path, filename)
    try:
        data = pd.read_csv(file_path, sep=sep,
                           **kwargs)
        return (data)
    except FileNotFoundError:
        print ('File not found: {}'.format(file_path))
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT),filename)

def aggregate(data: pd.DataFrame, 
    grouper: list=['PERIOD'],
    column: str='GenCapacity') -> pd.DataFrame:
    """ Groupby function to get the sum of each technology
    """
    try:
        df = data.groupby(grouper)[column].sum()
        return (df)
    except KeyError as ex:
        raise KeyError('Key {0} Not found in DataFrame'.format(ex))

def create_dict_by_category(data: pd.DataFrame, category: str='PERIOD') -> dict:

    df = data.groupby(category)
    return {key: value for key, value in df}

if __name__ == '__main__':
    filename = 'gen_cap.txt'
    df = get_data(filename=filename)
    df_sum = aggregate(df)
    dict_ = create_dict_by_category(df)
    print (df_sum.head())