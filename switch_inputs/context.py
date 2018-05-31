import os
import sys

script_path = os.path.dirname(__file__)
parent_path = os.path.dirname(os.path.dirname(__file__))
data_path = os.path.join(parent_path, 'data/clean/loads')
default_path = os.path.join(parent_path, 'data/default/')
output_path  = os.path.join(parent_path, 'data/switch_inputs/')
