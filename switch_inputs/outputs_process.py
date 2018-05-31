"""
Processing outputs
Ported from R to Python

"""

import os
import errno
import pandas as pd

script_path = os.path.dirname(__file__)
parent_path = os.path.dirname(os.path.dirname(__file__))
data_path = os.path.join(parent_path, 'data/')
output_path  = os.path.join(parent_path, 'data/clean/switch_outputs')

def get_data(path: os.PathLike=output_path, filename: str=None,
        *args, **kwargs) -> pd.DataFrame:
    """
    Get output data from folder
    Returns: Pandas Dataframe
    """

    # Get File path
    file_path =  os.path.join(path, filename)

    # Check if file exist
    if os.path.isfile(file_path):
        return (pd.read_csv(file_path, **kwargs))
    else:
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT),
                file_path)

def fix_typos(data: pd.DataFrame) -> pd.DataFrame:
    """ This function cleans the typos and prepare the data
    """


def main():
    """TODO: Docstring for main.
    :returns: TODO

    """
    dispatch_filename = 'dispatch.txt'
    dispatch = get_data(filename=dispatch_filename, sep='\t')
    print (dispatch.head())

if __name__ == "__main__":
    main()
