# data access
import sqlalchemy as sa

# data mungling
import pandas as pd

# local
from . import rt

# system
import pickle

logger = rt.logger

class DB():

    def __init__(self):

        self.md_tabs = None
        self.md_cols = None

        self.df_okved = None
        self.df_okved2 = None

        self.df_org = None
        self.df_declr = None
        self.df_bld = None

        # electricity consumption
        self.df_ee = None

        # water consumption
        self.df_cw = None
        self.df_hw = None

        # heat consumption
        self.df_heat = None

    def get_orgs(self):

        # declarations
        stmt = sa.sql.text('''
        select o.*,
               o2.label top_org_label,
               o2.is_municipality top_org_is_municipality, -- (1 - ОМСУ, 0 - ЦИОГВ)
               voc_okved.code okved_code, voc_okved.label okved_label,
               voc_okved2.code okved_code2, voc_okved2.label okved_label2
          from orgs o left join voc_okved  on o.id_voc_okved = voc_okved.id
                      left join voc_okved2 on o.id_voc_okved2 = voc_okved2.id
               left join orgs o2 on o.id_org_top = o2.id
         where o.fake = 0
        ''')

        df = pd.read_sql_query(stmt, con=rt.db_engine['energy'], index_col='id')
        logger.debug('Have fetched %d records of organizations.' % len(df))

        for col_name in ['top_org_is_municipality']:
            df[col_name] = df[col_name].astype('category')

        return(df)


    def get_declrs(self):

        """
        id_declr_status in (60, 90) - approved
        """

        # declarations
        stmt = sa.sql.text('''
        select d.*, voc_okved.code main_okved_code, voc_okved.label main_okved_label
          from declrs d left join orgs o on d.id_org = o.id left join voc_okved on o.id_voc_okved = voc_okved.id
         where d.fake = 0
        ''')

        df = pd.read_sql_query(stmt, con=rt.db_engine['energy'], index_col='id')
        logger.debug('Have fetched %d records of declarations.' % len(df))

        return(df)


    def get_declr_building(self):

        """
        Returns declarations along with buildings, includes relative statistics of the consumption
        """

        stmt = sa.sql.text('''
        select d.year,
               bld.id_declr,
               bld.id id_declr_building,
               d.id_org,
               d.inn,
               bld.id_org_building,
               bld.actual_address,
               
               org_buildings.id_voc_building_own,
               
               org_buildings.id_voc_building_function_type,
               org_buildings.id_voc_building_type,
               
               org_buildings.floor_area,
               org_buildings.useful_area,
               org_buildings.heated_area,
               org_buildings.total_value,
               org_buildings.floor_amount,
               
               org_buildings.launch_year,
               org_buildings.overhaul_year,
               org_buildings.maintenance_year,
               d.year-bld.launch_year building_age,
               
               case when
                10 in (select id_voc_outer_walls from declr_voc_outer_walls where fake = 0 and id_org_building = org_buildings.id and id_declr_building is null)
                  then '10'
                else
                  (select string_agg(id_voc_outer_walls::text, ', ' order by id_voc_outer_walls) from (select distinct id_voc_outer_walls from declr_voc_outer_walls where fake = 0 and id_org_building = org_buildings.id and id_declr_building is null) t1)
                end
                as id_voc_outer_walls_list,

               org_buildings.front_insulated,

               (select string_agg(id_voc_windows::text, ', ' order by id_voc_windows) from (select distinct id_voc_windows from declr_voc_windows where fake = 0 and id_org_building = org_buildings.id and id_declr_building is null) t2) as id_voc_windows_list,
               org_buildings.id_voc_windows_glazing,
               org_buildings.windows_glazing_coverage,
               org_buildings.windows_other,
               org_buildings.id_voc_windows_wood,
               org_buildings.single_door_amount,
               org_buildings.double_door_amount,
               org_buildings.entrance_amount,
               org_buildings.vestibule_amount,
               org_buildings.door_closer_amount,
               org_buildings.air_curtain_amount,
               org_buildings.air_curtain_manual_amount,
               org_buildings.air_curtain_auto_amount,
               org_buildings.roof_exists,
               org_buildings.roof_frost,
               org_buildings.roof_insulated,
               org_buildings.roofing_metal_insulated,
               org_buildings.roofing_soft_single_insulation,
               org_buildings.attic_exists,
               org_buildings.attic_insulated,
               org_buildings.attic_pipe_insulated,
               org_buildings.technical_floor_exists,
               org_buildings.basement_exists,
               org_buildings.basement_cold,
               org_buildings.basement_damp,
               org_buildings.basement_walls_freeze,
               org_buildings.basement_glazing,
               org_buildings.basement_pipe_insulated,
               org_buildings.id_voc_boiler_control,
               org_buildings.meter_heat_inputs_commercial,
               org_buildings.id_voc_heat_piping,
               org_buildings.cast_iron_heater_amount,
               org_buildings.convectors_amount,
               org_buildings.convectors_with_thermostatic_flow_control,
               org_buildings.bimetal_heater_amount,
               org_buildings.thermostatic_control_heater_amount,
               org_buildings.individual_control_heater_amount,
               org_buildings.additional_heater_amount,
               org_buildings.other_heaters_amount,
               org_buildings.central_ventilation_exists,
               org_buildings.employees,
               org_buildings.guests,
               org_buildings.central_dispatching_exists,
               bld.heat_points,
               -- cold water
               --cw.cold_water_consumption, cw.cold_water_payment,
               -- hot water
               --hw.hot_water_consumption,  hw.hot_water_payment,
               -- cold water
               --ee.electric_consumption,    ee.electric_payment,
               -- heat
               ht.heat_consumption, ht.heat_payment,
               -- OKVED
               voc_okved.code main_okved_code, voc_okved.label main_okved_label
          from declr_buildings bld
               inner join declrs d on bld.id_declr = d.id
               inner join org_buildings on bld.id_org_building = org_buildings.id AND org_buildings.id_voc_building_own <> 2
               inner join orgs o on d.id_org = o.id left join voc_okved on o.id_voc_okved = voc_okved.id
               left join voc_building_types   on bld.id_voc_building_type = voc_building_types.id
               -- adding the cold water consumption
               left join (select id_declr, id_declr_building,
                                 sum(cold_water_consumption) cold_water_consumption,
                                 sum(cold_water_payment) cold_water_payment                                 
                            from declr_cold_water 
                           where fake = 0
                           group by id_declr, id_declr_building) cw 
                    on bld.id = cw.id_declr_building and bld.id_declr = cw.id_declr
               -- adding the hot water consumption
               left join (select id_declr, id_declr_building,
                                 sum(hot_water_consumption) hot_water_consumption,
                                 sum(hot_water_payment) hot_water_payment                                 
                            from declr_hot_water 
                           where fake = 0
                           group by id_declr, id_declr_building) hw
                    on bld.id = hw.id_declr_building and bld.id_declr = hw.id_declr
               -- adding the electricity consumption
               left join (select id_declr, id_declr_building,
                                 sum(electric_consumption) electric_consumption,
                                 sum(electric_payment) electric_payment                                 
                            from declr_electric
                           where fake = 0
                           group by id_declr, id_declr_building) ee 
                    on bld.id = ee.id_declr_building and bld.id_declr = ee.id_declr
               -- adding the heat consumption
               left join (select id_declr, id_declr_building, 
                                 sum(heat_consumption) as heat_consumption, 
                                 sum(heat_payment) as heat_payment 
                                from declr_heat where fake = 0 group by 1, 2) ht 
                    on bld.id = ht.id_declr_building and bld.id_declr = ht.id_declr
         where d.fake    = 0
           and bld.fake  = 0
           and o.fake    = 0
           and voc_okved.fake = 0
         order by bld.id_declr, bld.id
        ''')

        df = pd.read_sql_query(stmt, con=rt.db_engine['energy'], index_col='id_declr_building')
        logger.debug('Have fetched %d records of declarations of buildings.' % len(df))

        for col_name in ['year',
                         'front_insulated',
                         'roof_exists', 'roof_insulated',
                         'attic_exists', 'attic_insulated', 'attic_pipe_insulated',
                         'basement_exists', 'basement_cold', 'basement_damp',
                         'basement_walls_freeze', 'basement_glazing', 'basement_pipe_insulated']:
            df[col_name] = df[col_name].astype('category')

        # adding information of the municipality
        df = df.merge(self.df_org['top_org_is_municipality'], left_on='id_org', right_index=True, how='left')

        # adding our own features
        #df['electric_consumption_per_employee']   = df['electric_consumption']   / (df['employees'] + 1)
        #df['cold_water_consumption_per_employee'] = df['cold_water_consumption'] / (df['employees'] + 1)
        #df['hot_water_consumption_per_employee']  = df['hot_water_consumption']  / (df['employees'] + 1)
        df['heat_consumption_per_heated_area']    = df['heat_consumption']       / (df['heated_area'] + 1)

        # checking there are no duplicates per id
        assert "There are duplicates of id_declr_building's", (df.index.value_counts() > 1).mean() == 0

        return(df)

    def get_electricity_stats(self):

        """
        Returns electric consumption
        """

        stmt = sa.sql.text('''
        select *
          from declr_electric
         where fake = 0
           and id_declr_building > 0
           and id_declr_workshop = 0;
        ''')

        df = pd.read_sql_query(stmt, con=rt.db_engine['energy'], index_col='id')

        logger.debug('Have read %d records of the electricity consumption.' % len(df))

        return(df)


    def get_heat_stats(self):

        """
        Returns electric consumption
        """

        stmt = sa.sql.text('''
        select *
          from declr_heat
         where fake = 0
           and id_declr_building > 0
           and id_declr_workshop = 0;
        ''')

        df = pd.read_sql_query(stmt, con=rt.db_engine['energy'], index_col='id')

        logger.debug('Have read %d records of the heat consumption.' % len(df))

        return(df)


    def get_cold_water_stats(self):

        """
        Returns consumption
        """

        stmt = sa.sql.text('''
        select *
          from declr_cold_water
         where fake = 0
           and id_declr_building > 0   -- id_declr_building equal to 0 is the sum of consumption for all buildings
           and id_declr_workshop = 0;  -- this excludes workshops
        ''')

        df = pd.read_sql_query(stmt, con=rt.db_engine['energy'], index_col='id')

        logger.debug('Have read %d records of the cold water consumption.' % len(df))

        return(df)


    def get_hot_water_stats(self):

        """
        Returns consumption
        """

        stmt = sa.sql.text('''
        select *
          from declr_hot_water
         where fake = 0
           and id_declr_building > 0
           and id_declr_workshop = 0;
        ''')

        df = pd.read_sql_query(stmt, con=rt.db_engine['energy'], index_col='id')

        logger.debug('Have read %d records of the hot water consumption.' % len(df))

        return(df)


    def get_local_db_config(self):

        # local db config
        local_db_config = {

            'md_tabs':   {'df': self.md_tabs,   'file_name': 'md_tabs.{}'},
            'md_cols':   {'df': self.md_cols,   'file_name': 'md_cols.{}'},

            'df_okved':  {'df': self.df_okved,  'file_name': 'df_okved.{}'},
            'df_okved2': {'df': self.df_okved2, 'file_name': 'df_okved2.{}'},

            'df_org':    {'df': self.df_org,    'file_name': 'df_org.{}'},
            'df_declr':  {'df': self.df_declr,  'file_name': 'df_declr.{}'},
            'df_bld':    {'df': self.df_bld,    'file_name': 'df_bld.{}'},

            'df_ee':     {'df': self.df_ee,     'file_name': 'df_ee.{}'},
            'df_cw':     {'df': self.df_cw,     'file_name': 'df_cw.{}'},
            'df_hw':     {'df': self.df_hw,     'file_name': 'df_hw.{}'},
            'df_heat':   {'df': self.df_heat,   'file_name': 'df_heat.{}'},
        }

        return(local_db_config)


    def load_pg(self, data_parts):

        #
        # Table Description
        #
        stmt = sa.sql.text('''
        select table_name, obj_description(table_name::regclass)
          from information_schema.tables t
         where t.table_catalog = 'energy_prod'
           and t.table_schema = 'public'
         order by table_name;
        ''')
        self.md_tabs = pd.read_sql_query(stmt, con=rt.db_engine['energy'])
        logger.debug(f'Loaded the tables metadata of the shape {self.md_tabs.shape}')

        #
        # Column Description
        #
        stmt = sa.sql.text('''
        select table_name,
               column_name,
               (select pg_catalog.col_description(c.oid, cols.ordinal_position :: int)
                  from pg_catalog.pg_class c
                 where c.oid = (select ('"' || cols.table_name || '"') :: regclass :: oid)
                   and c.relname = cols.table_name) as column_comment
          from information_schema.columns cols
         where cols.table_catalog = 'energy_prod'
           and cols.table_schema = 'public'
         order by table_name;
        ''')
        self.md_cols = pd.read_sql_query(stmt, con=rt.db_engine['energy'])
        logger.debug(f'Loaded the columns metadata of the shape {self.md_cols.shape}')

        #
        # OKVED
        #
        stmt = sa.sql.text('''
        select *
          from voc_okved
        ''')
        self.df_okved = pd.read_sql_query(stmt, con=rt.db_engine['energy'])
        logger.debug(f'Loaded OKVED of the shape {self.df_okved.shape}')

        #
        # OKVED2
        #
        stmt = sa.sql.text('''
        select *
          from voc_okved2
        ''')
        self.df_okved2 = pd.read_sql_query(stmt, con=rt.db_engine['energy'])
        logger.debug(f'Loaded OKVED2 of the shape {self.df_okved2.shape}')

        #
        # Information of Organization
        #
        self.df_org = self.get_orgs()

        #
        # Information of Organization
        #
        self.df_declr = self.get_declrs()

        #
        # Information of Organization
        #
        self.df_bld = self.get_declr_building()

        # electricity consumption
        self.df_ee = self.get_electricity_stats()

        # cold water consumption
        self.df_cw = self.get_cold_water_stats()

        # hot water consumption
        self.df_hw = self.get_hot_water_stats()

        # heat consumption
        self.df_heat = self.get_heat_stats()

        #return(self)


    def load_local(self, data_parts, format_type='pickle'):

        local_db_config = self.get_local_db_config()

        for df_name, item in local_db_config.items():

            full_path = '{}{}'.format(rt.config['common']['local_db_dir'], item['file_name'].format(format_type))

            logger.debug('Loading {} from {}'.format(df_name, full_path))

            #item['df'].to_parquet(full_path)
            if format_type == 'parquet':
                item['df'] = pd.read_parquet(full_path)
            elif format_type == 'pickle':
                # with open(full_path, 'rb') as f:
                #     item['df'] = pickle.load(f)
                    # eval(f'self.{df_name} = item[\'db\'].copy()')
                item['df'] = pd.read_pickle(full_path)
            logger.debug('Loaded.')

        # the above is not working properly so sticking in this dirty hack
        self.df_org    = local_db_config['df_org']['df']
        self.df_declr  = local_db_config['df_declr']['df']
        self.df_bld    = local_db_config['df_bld']['df']
        self.md_cols   = local_db_config['md_cols']['df']
        self.df_okved  = local_db_config['df_okved']['df']
        self.df_okved2 = local_db_config['df_okved2']['df']

    def load(self, source, data_parts=('all')):

        if source == 'pg':
            self.load_pg(data_parts=data_parts)
        elif source == 'local':
            self.load_local(data_parts=data_parts)
        else:
            raise ValueError

    def save_local(self, dest='local', format_type='pickle'):

        local_db_config = self.get_local_db_config()

        for df_name, item in local_db_config.items():

            full_path = '{}{}'.format(rt.config['common']['local_db_dir'], item['file_name'].format(format_type))

            logger.debug('Saving {} to {}'.format(df_name, full_path))

            if item['df'] is None:
                logger.debug('It is empty.')
            else:
                #item['df'].to_parquet(full_path)
                if format_type == 'parquet':
                    item['df'].to_parquet(full_path)
                elif format_type == 'pickle':
                    item['df'].to_pickle(full_path)
                    # with open(full_path, 'wb') as f:
                    #     pickle.dump(item['df'], f)
                logger.debug('Saved.')

    def save(self, dest='local', data_parts=('all')):

        if dest == 'local':
            self.save_local(format_type='pickle')
        else:
            raise ValueError

