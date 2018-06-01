import sys
import click
import requests
from __version__ import __version__
from tqdm import tqdm
from context import *
from utils import init
from utils import read_yaml, init_scenario
from utils import create_gen_build_cost_new, look_for_file
from create_inputs import *

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])

def print_version(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    version = __version__
    click.echo(f'Switch Inputs {version}')
    ctx.exit()

@click.group(invoke_without_command=True)
@click.option('--version', is_flag=True, callback=print_version,
              expose_value=False, is_eager=True)
@click.option('--debug/--no-debug', default=False)
@click.pass_context
def main(ctx, debug):
    # FIXME: For some reason this does not work properly
    #  ctx.obj['DEBUG'] = debug
    pass

@main.command()
@click.option('--number', default=4, prompt='Number of timepoints',
                help='Number of timepoints possible [1, 2, 3, 4, 6, 8, 12]')
@click.option('--existing/--no-existing',
              default=True,
              prompt='Include existing plants',
              help='Add existing plants to the analysis')
@click.option('--proposed/--no-proposed',
              default=True,
              prompt='Include proposed plants',
              help='Add new plants to the analysis')
@click.option('--load', type=click.Choice(['low', 'medium', 'high']),
              prompt='Select load profile',
              default='high',
              help='Load profile to use')
@click.pass_context
def create(ctx, number, existing, proposed, load, path=default_path, **kwargs):
    """ Main function that creates all the inputs 🔥"""

    #  if ctx.obj['DEBUG']:
    #      def debug(type, value, tb):
    #          import traceback, pdb
    #          traceback.print_exception(type, value, tb)
    #          pdb.pm()
    #      sys.excepthook = debug

    click.echo('Starting app')

    if existing and proposed:
        click.echo('Creating generation project info')
        gen_project_legacy = pd.read_csv(os.path.join(default_path,
            'generation_projects_info.tab'), sep='\t')
        gen_project_proposed = init_scenario()
        gen_project = pd.concat([gen_project_legacy, gen_project_proposed])
        gen_legacy = gen_build_predetermined(existing)
        create_gen_build_cost(gen_project, gen_legacy)
    else:
        click.echo('Oops I do not know what to do yet')
        sys.exit(1)

    # Finally
    gen_project.to_csv(os.path.join(output_path,
        'generation_projects_info.tab'),
        sep='\t', index=False)

    click.echo(f'Number of timepoints selected: {number}')

    click.echo(f'Reading load data')
    load_data = get_load_data(filename=load)

    click.echo(f'Reading periods data')
    periods = read_yaml(path, 'periods.yaml')

    d = OrderedDict(periods)
    periods_tab = pd.DataFrame(d)
    periods_tab = periods_tab.set_index('INVESTMENT_PERIOD')

    click.echo(f'Creating timeseries')
    timeseries, timeseries_dict = [], {}
    for periods, row in periods_tab.iterrows():
        timeseries_dict[periods] = []
        scale_to_period = row[1] - row[0]
        peak_data = get_peak_day(load_data[str(periods)]['total'], number, freq='1MS', **kwargs)
        median_data = get_median_day(load_data[str(periods)]['total'], number, freq='1MS', **kwargs)
        timeseries_dict[periods].append(create_strings(peak_data, scale_to_period))
        timeseries_dict[periods].append(create_strings(median_data, scale_to_period,
                                        identifier='M'))
        timeseries.append(create_strings(peak_data, scale_to_period))
        timeseries.append(create_strings(median_data, scale_to_period,
                                        identifier='M'))
    click.echo(f'Creating investment period')
    create_investment_period()

    #  create_gen_build_cost_new(peak_data)
    create_timeseries(timeseries, number, **kwargs)
    create_timepoints(timeseries)
    click.echo(f'Creating variable capacity factor')
    create_variablecp(gen_project, timeseries, timeseries_dict)
    click.echo(f'Creating loads')
    create_loads(load_data, timeseries)

    rps_file, ext = look_for_file('rps_targets', default_path)

    click.echo(f'Creating fuel loads')
    create_fuel_cost()
    if rps_file:
        click.echo(f'Creating rps')
        create_rps(filename=rps_file, ext=ext)

    click.echo(f'App ended')

main.add_command(init)

if __name__ == "__main__":
    main(obj={})
