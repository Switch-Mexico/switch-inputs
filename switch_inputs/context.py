import os
import sys
from pathlib import Path

script_path = os.path.dirname(__file__)
parent_path = os.path.dirname(os.path.dirname(__file__))
data_path = os.path.join(parent_path, 'data/clean/loads')
default_path = os.path.join(parent_path, 'data/default/')
default_path = Path('data/default/')
output_path  = os.path.join(parent_path, 'data/switch_inputs/')
output_path  = Path('data/switch_inputs/')
