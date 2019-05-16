# data mungling
import pandas as pd

# local
from . import rt

logger = rt.logger

class Filter():

    def __init__(self):

        self.filters = []

    def add(self, name, fn, seq=None):

        """
        Add a filter
        :return:
        """

        if seq is None:

            seq = len(self.filters)

        self.filters.insert(seq, {'name': name ,'fn': fn})

    def transform(self, df):

        """
        Apply all filters in their order
        :return:
        """

        dfr = df

        for f in self.filters:
            name = f['name']
            try:
                dfr = f['fn'](dfr)
                data_left_pct = 100 * len(dfr) / len(df)
                logger.info(f'Applied the filter {name:32s}, the data left: {data_left_pct:.2f}%')
            except Exception as e:
                logger.info(f'Tried the filter   {name:32s}, encountered an exception')
                raise(e)

        return(dfr)

    def __str__(self):

        out = ''

        if len(self.filters) == 0:
            out = 'No filters'
        else:
            for i, f in enumerate(self.filters):
                name, fn = f['name'], f['fn']
                out = out + f'{i}: {name}, {fn}\n'

        return(out)


# with only heat consumption
def f_bld_hc_exists(df):
    dfr = df.query('heat_consumption > 0')

    return (dfr)


# with known and reasonable area values
def f_bld_hc_areas(df, quantiles=(0.05, 0.95)):
    """
    Filter by areas
    """

    lower_quantile = quantiles[0]
    upper_quantile = quantiles[1]

    dft = df.query('floor_area >= heated_area') \
        .query('floor_area >= useful_area') \
        .query('useful_area > 0 and heated_area > 0 and total_value > 0') \
        .query('entrance_amount > 0') \
        .query('heated_area > 0 and heat_consumption > 0 and heat_payment > 0') \
        .query('floor_amount > 0') \
        .loc[lambda x: x['floor_area'] >= x['floor_area'].quantile(lower_quantile)] \
        .loc[lambda x: x['floor_area'] <= x['floor_area'].quantile(upper_quantile)] \
        .loc[lambda x: x['heated_area'] >= x['heated_area'].quantile(lower_quantile)] \
        .loc[lambda x: x['heated_area'] <= x['heated_area'].quantile(upper_quantile)] \
        .loc[lambda x: x['useful_area'] >= x['useful_area'].quantile(lower_quantile)] \
        .loc[lambda x: x['useful_area'] <= x['useful_area'].quantile(upper_quantile)] \
        .loc[lambda x: x['total_value'] >= x['total_value'].quantile(lower_quantile)] \
        .loc[lambda x: x['total_value'] <= x['total_value'].quantile(upper_quantile)]

    return (dft)


###############################################################################
# Filters
###############################################################################

# leaving only those without significant inconsistency in reporting
def f_bld_hc_consistency(df):
    """
    By inconsistency in reporting the heat consumption
    """

    # number of years
    years_count = len(df['year'].drop_duplicates())

    # get_valid_records
    df_bld_ht_diff = df.sort_values(['id_org_building', 'year']) \
        .groupby(['id_org_building'])['year', 'id_org_building', 'heat_consumption'] \
        .filter(lambda x: len(x['heat_consumption']) == years_count and (x['heat_consumption'] > 0).all()) \
        .groupby(['id_org_building'])['heat_consumption'] \
        .apply(lambda x: x.max() / x.min())

    df_bld_ht_good_cases = df_bld_ht_diff.loc[lambda x: x > 1].loc[lambda x: x <= 3]

    # logger.debug('Min/max ratios for all cases:  {:.1f}, {:.1f}'.format(df_bld_ht_diff.min(), df_bld_ht_diff.max()))
    # logger.debug('Min/max ratios for good cases: {:.1f}, {:.1f}'.format(df_bld_ht_good_cases.min(), df_bld_ht_good_cases()))

    dft = df[df['id_org_building'].isin(df_bld_ht_good_cases.index)].copy()

    return (dft)


def f_bld_hc_no_outliers(df, quantiles=(0.05, 0.95)):
    """
    By extreme values in the heat consumption (per the heated area)
    """

    lower_quantile = quantiles[0]
    upper_quantile = quantiles[1]

    dft = df.query('heat_consumption_per_heated_area > 0') \
        .loc[lambda x: x['heat_consumption_per_heated_area'] >= x['heat_consumption_per_heated_area'].quantile(
        lower_quantile)] \
        .loc[lambda x: x['heat_consumption_per_heated_area'] <= x['heat_consumption_per_heated_area'].quantile(
        upper_quantile)]

    return (dft)


def f_bld_hc_inputs_commercial(df):
    """
    There number of meters is not extreme
    """

    dft = df.query('meter_heat_inputs_commercial <= 3')

    return (dft)


def f_bld_hc_inputs_com_exists(df):
    """
    There are meters
    """

    dft = df.query('meter_heat_inputs_exists')

    return (dft)

def f_bld_hc_employees(df):
    """
    There are employees
    """

    dft = df.query('employees > 0')

    return (dft)


###############################################################################
# Imputers
###############################################################################

def i_bld_impute(df):

    df['dd_okved'] = df['dd_okved'].fillna('-1')

    # there is no boiler control
    df['id_voc_boiler_control'] = df['id_voc_boiler_control'].fillna(-1)

    # we don't know the type of wood windows
    df['id_voc_windows_wood'] = df['id_voc_windows_wood'].fillna(-1)

    # TODO: windows_glazing_coverage can be filled with a median value if id_voc_windows_glazing has certain value
    df['windows_glazing_coverage'] = df['windows_glazing_coverage'].fillna(0)
    df['id_voc_windows_glazing'] = df['id_voc_windows_glazing'].fillna(-1)

    df['id_voc_heat_piping'] = df['id_voc_heat_piping'].fillna(-1)

    df['other_heaters_amount'] = df['other_heaters_amount'].fillna(0)

    df['convectors_with_thermostatic_flow_control'] = df['convectors_with_thermostatic_flow_control'].fillna(0)
    df['convectors_amount'] = df['convectors_amount'].fillna(0)
    df['thermostatic_control_heater_amount'] = df['thermostatic_control_heater_amount'].fillna(0)
    df['additional_heater_amount'] = df['additional_heater_amount'].fillna(0)
    df['individual_control_heater_amount'] = df['individual_control_heater_amount'].fillna(0)
    df['bimetal_heater_amount'] = df['bimetal_heater_amount'].fillna(0)
    df['air_curtain_auto_amount'] = df['air_curtain_auto_amount'].fillna(0)
    df['air_curtain_manual_amount'] = df['air_curtain_manual_amount'].fillna(0)
    df['air_curtain_amount'] = df['air_curtain_amount'].fillna(0)

    df['id_voc_building_function_type'] = df['id_voc_building_function_type'].fillna(-1)

    df['cast_iron_heater_amount'] = df['cast_iron_heater_amount'].fillna(0)

    df['double_door_amount'] = df['double_door_amount'].fillna(0)
    df['single_door_amount'] = df['single_door_amount'].fillna(0)
    df['door_closer_amount'] = df['door_closer_amount'].fillna(0)
    df['vestibule_amount'] = df['vestibule_amount'].fillna(0)

    df['id_voc_windows_list'] = df['id_voc_windows_list'].fillna(-1)

    df['id_voc_outer_walls_list'] = df['id_voc_outer_walls_list'].fillna(-1)

    # imputting based on an average value within the same OKVED
    for attr in ('entrance_amount', 'floor_amount',
                 'floor_area', 'heated_area', 'useful_area', 'total_value',
                 'guests', 'employees'):
        df[attr] = df.groupby('dd_okved')[attr].transform(lambda x: x.fillna(x.median()))

    return (df)


def t_bld_categorize(df):

    for col_name in (
            'id_voc_building_function_type',
            'id_voc_building_type',
            'id_voc_outer_walls_list',
            'front_insulated',
            'id_voc_windows_list',
            'id_voc_windows_glazing',
            'id_voc_windows_wood',
            'roof_exists',
            'roof_frost',
            'roof_insulated',
            'roofing_metal_insulated',
            'roofing_soft_single_insulation',
            'attic_exists',
            'attic_insulated',
            'attic_pipe_insulated',
            'technical_floor_exists',
            'basement_exists',
            'basement_cold',
            'basement_damp',
            'basement_walls_freeze',
            'basement_glazing',
            'basement_pipe_insulated',
            'id_voc_boiler_control',
            'id_voc_heat_piping',
            'central_ventilation_exists',
            'central_dispatching_exists',
            'main_okved_code',
            'top_org_is_municipality',
            'meter_heat_inputs_exists',
            'ya_climate_zone',
            'dd_okved_code_l1'
    ):
        df[col_name] = df[col_name].astype('category')

    return(df)