import streamlit as st
import datetime as dt
import numpy as np
from streamlit_echarts import st_echarts
import pandas as pd
import main
import altair as alt
import json
import os
import base64
from datetime import datetime


def csv_to_json():
    data_dict = {}
    data = pd.read_csv('heatload.csv')

    for column in data.columns:
        data_dict[column] = list(data[column].values)
    with open('heatload.json', 'w', encoding='utf-8') as json_file_handler:
        json_file_handler.write(json.dumps(data_dict, separators=(',', ':'), indent=4))


st.set_page_config(
    page_title="Thermal Loads",
    page_icon=":sun:",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items=None)

# TODO change absolut path to relative: 1) var.py --> Row 27&71 2) Wea.py --> Row 91
# streamlit run /Users/renekeding/Desktop/Uni/Master/2Semester/EVEESS22/Code/EVEE-main_rene/GUI_inputs.py

# building standards
standards = ['unsaniert', 'WSchV 95', 'EnEV 2009', 'EnEV 2014', 'GEG', 'KN45', 'KN30']

# Temperature units
tmp_units = ['°C', '°K', '°F']

# Wetter APIs
weather_apilist = ['Deutscher Wetterdienst', 'Visual Crossing']

###BUILD APP

# workaround to set width of app to 75%, commeted out as the sankey diagram is not shown properly with it
# taken from https://discuss.streamlit.io/t/where-to-set-page-width-when-set-into-non-widescreeen-mode/959/15
# st.markdown(
#        f"""
# <style>
#    .appview-container .main .block-container{{
#        max-width: 75%;
#    }}
# </style>
# """,
#        unsafe_allow_html=True,
#    )

st.title('Thermal load time-series Project')
st.header('EVEEE WiSe 23/24')

# Build first Streamlit Interface with Input Variables
with st.expander('Input Variables', expanded=True):  # Expander
    # Form 1 --> Send all input variables to simulation together, instead of each variable seperate
    with st.form(key='1'):

        st.subheader('Building Parameters')
        # Building lenght, width and height inputs
        col1, col2, col3 = st.columns(3)
        l = col1.number_input(label='Length of Building [m]', step=1, min_value=1, max_value=10, value=5, key='l')
        b = col2.number_input(label='Width of Building [m]', step=1, min_value=1, max_value=10, value=5, key='b')
        h = col3.number_input(label='Height of Building [m]', step=1, min_value=1, max_value=30, value=5, key='h')

        # Building floors, occupants and standard inputs
        col1, col2, col3 = st.columns(3)
        # Get the number of floors from user input
        num_floors = col1.number_input(label='Number of Floors', step=1, min_value=1, max_value=10, key='floors')
        # occupants = col2.number_input(label='Number of Occupants', step=1, min_value=1, max_value=10, value=2,
        # key='occupants')
        bldstd = col2.selectbox(label='Building Standard', options=standards, key='bldstd')

        # Create a list to store the temperature inputs for each floor
        # occupants_inputs = []
        # col1, col2, col3 = st.columns(3)
        # col1.markdown(f'Enter Number of Occupants (Floor 1)')
        # occ = col2.number_input(label='Number of Occupants', step=1, min_value=1, max_value=10, value=2,
        #                        key=f'occupants_1')
        # occupants_inputs.append(occ)

        # if submitbutton or num_floors > 1:
            # Generate the temperature input fields dynamically
        #    for floor in range(1, num_floors):
        #        col1, col2, col3 = st.columns(3)
        #        col1.markdown(f'Enter Number of Occupants (Floor {floor + 1})')
        #        occ = col2.number_input(label='Number of Occupants', step=1, min_value=1, max_value=10, value=2,
        #                                key=f'occupants_{floor + 1}')
        #        # Store the temperature inputs for each floor
        #        occupants_inputs.append(occ)
        # sum_occupants = sum(occupants_inputs)

        # Multiple Floors Single Zone (MFSZ) yet to be done

        # activity inputs for occupants
        st.markdown(
            'Enter heat emissions per occupant for day and night. If range is selected, random value between lower and upper bound is selected, otherwise lower bound as fixed value.')
        col1, col2, col3 = st.columns(3)
        act_day_range = col1.checkbox(label='Range Day On', value=True, key='act_day_range')
        act_day_lower = col2.number_input(label='Lower Value Day [W/Person]', step=5, value=100, min_value=0,
                                          key='act_day_lower')
        act_day_upper = col3.number_input(label='Upper Value Day [W/Person]', step=5, value=125, min_value=0,
                                          key='act_day_upper')
        col1, col2, col3 = st.columns(3)
        act_night_range = col1.checkbox(label='Range Night On', value=False, key='act_night_range')
        act_night_lower = col2.number_input(label='Lower Value Night [W/Person]', step=5, value=80, min_value=0,
                                            key='act_night_lower')
        act_night_upper = col3.number_input(label='Upper Value Night [W/Person]', step=5, value=80, min_value=0,
                                            key='act_night_upper')
        st.markdown('Enter time interval at which night activity starts and ends')
        col1, col2 = st.columns(2)
        act_night_start = col1.number_input(label='Start Time of Night Activity [h]', step=1, value=23, min_value=0,
                                            max_value=24, key='act_night_start')
        act_night_end = col2.number_input(label='End Time of Night Activity [h]', step=1, value=6, min_value=0,
                                          max_value=24, key='act_night_end')



        # st.markdown('Enter the sum of the window to wall ratio (Floor 1)')
        # floor_wtw_ratio = st.slider('Sum of Window to Wall Ratio for all direction', min_value=0, max_value=4,
        #                           value=0, step=0.01, key='wtwr_slider')
        col1, col2, col3 = st.columns(3)
        # Create Submit Button 1
        submitbutton = col1.form_submit_button("Update Number of Input-Fields")

        # Gather Floor information, i.e. Zones and Occupants
        # Single Floor Multi Zone (SFMZ)
        st.subheader('Floor Characteristics')
        st.markdown('Enter the number of zones for each floor, number of occupants in each of these zones and the '
                    'window to wall ratio of each of the zones')
        # occupants_inputs = []
        floor_all_occ_inputs = []
        zone_occupants_inputs = []
        floor_all_wtwr_inputs = []
        zone_wtwr_inputs = [] # Window to Wall Ratio in the format [North, South, East, West]
        # col1, col2 = st.columns(2)
        if submitbutton:
            for floor in range(1, num_floors + 1):
                col1, col2 = st.columns(2)
                col1.write(f'**Floor {floor}**')
                col1, col2 = st.columns(2)
                col1.markdown(f'Enter Number of Zones (Floor {floor}) and Update Field')
                num_of_zones = col2.number_input(label='Number of Zones', step=1, min_value=1, max_value=6, value=1,
                                                 key=f'zones_{floor}')
                st.markdown('Enter Window to Wall ratio for all directions in each zone')
                for zone in range(1, num_of_zones + 1):
                    col1, col2, col3 = st.columns(3)
                    col1.markdown(f'Zone {zone}')
                    zone_wtwr_n = col2.slider('North', min_value=0.0, max_value=1.0, value=0.0, step=0.01,
                                                      key=f'zone_wtwr_n_{floor}_{zone}')
                    zone_wtwr_s = col2.slider('South', min_value=0.0, max_value=1.0, value=0.0, step=0.01,
                                                      key=f'zone_wtwr_s_{floor}_{zone}')
                    zone_wtwr_e = col2.slider('East', min_value=0.0, max_value=1.0, value=0.0, step=0.01,
                                                     key=f'zone_wtwr_e_{floor}_{zone}')
                    zone_wtwr_w = col2.slider('West', min_value=0.0, max_value=1.0, value=0.0, step=0.01,
                                                     key=f'zone_wtwr_w_{floor}_{zone}')
                    zone_occ = col3.number_input(label='Number of Occupants', step=1, min_value=1, max_value=10,
                                                 value=2,
                                                 key=f'occupants_{floor}_{zone}')
                    zone_wtwr = [zone_wtwr_n, zone_wtwr_s, zone_wtwr_e, zone_wtwr_w]
                    zone_wtwr_inputs.append(zone_wtwr)
                    zone_occupants_inputs.append(zone_occ)
                floor_all_wtwr_inputs.append(zone_wtwr_inputs)
                floor_all_occ_inputs.append(zone_occ)


        # if submitbutton or num_of_zones > 1:
        #    st.markdown('Enter Window to Wall ratio for all directions in each zone')
        #    for zone in range(1, num_of_zones + 1):
        #        col1, col2, col3 = st.columns(3)
        #        col1.markdown(f'Zone {zone}')
        #        zone_wtwr_dir_north = col2.slider('North', min_value=0.0, max_value=1.0, value=0.0, step=0.01,
        #                                          key=f'zone_wtwr_dir_north_{zone}')
        #        zone_wtwr_dir_south = col2.slider('South', min_value=0.0, max_value=1.0, value=0.0, step=0.01,
        #                                          key=f'zone_wtwr_dir_south_{zone}')
        #        zone_wtwr_dir_east = col2.slider('East', min_value=0.0, max_value=1.0, value=0.0, step=0.01,
        #                                         key=f'zone_wtwr_dir_east_{zone}')
        #        zone_wtwr_dir_west = col2.slider('West', min_value=0.0, max_value=1.0, value=0.0, step=0.01,
        #                                         key=f'zone_wtwr_dir_west_{zone}')
        #        zone_occ = col3.number_input(label='Number of Occupants', step=1, min_value=1, max_value=10, value=2,
        #                                     key=f'occupants_{zone}')
        #        zone_occupants_inputs.append(zone_occ)

        # window to wall ratios
        # wtw = [0] * 4
        # st.markdown(
        #    'Enter respective window to wall ratios for each building side. Default values are based on statistical data for Germany (Wiezorek(2012))')
        # col1, col2, col3, col4 = st.columns(4)
        # wtw[0] = col1.number_input(label='North', step=0.01, value=0.10, min_value=0.0, max_value=1.0, key='north')
        # wtw[1] = col2.number_input(label='East', step=0.01, value=0.15, min_value=0.0, max_value=1.0, key='east')
        # wtw[2] = col3.number_input(label='South', step=0.01, value=0.20, min_value=0.0, max_value=1.0, key='south')
        # wtw[3] = col4.number_input(label='West', step=0.01, value=0.15, min_value=0.0, max_value=1.0, key='west')


        # Building location (Latitude & Longitude) inputs
        col1, col2 = st.columns(2)
        lat = col1.number_input(label='Latitude', step=1., value=52.52, key='lat', help='For DWD Data within Germany!')
        lon = col2.number_input(label='Longitude', step=1., value=13.41, key='lon', help='For DWD Data within Germany!')

        st.subheader('Target Temperatures')

        # temperature comfort range & night setback inputs

        # Create a list to store the temperature inputs for each floor
        temp_min_inputs = []
        temp_max_inputs = []
        st.markdown('Enter lower and upper Bound for Temperature Comfort Zone (Zone 1)')
        col1, col2 = st.columns(2)
        tmp_min = col1.number_input(label='Lower Bound [°C]', step=1, value=17, key='tmp_min_1')
        tmp_max = col2.number_input(label='Upper Bound [°C]', step=1, value=20, key='tmp_max_1')
        temp_min_inputs.append(tmp_min)
        temp_max_inputs.append(tmp_max)
        if submitbutton or num_floors > 1:
            # Generate the temperature input fields dynamically
            for floor in range(1, num_floors):
                st.markdown(f'Enter lower and upper Bound for Temperature Comfort Zone (Zone {floor + 1})')
                col1, col2 = st.columns(2)
                tmp_min = col1.number_input(label='Lower Bound [°C]', step=1, value=17, key=f'tmp_min_{floor + 1}')
                tmp_max = col2.number_input(label='Upper Bound [°C]', step=1, value=20, key=f'tmp_max_{floor + 1}')

                # Store the temperature inputs for each floor
                temp_min_inputs.append(tmp_min)
                temp_max_inputs.append(tmp_max)

        # night setback inputs
        NSB_inputs = []
        NSB_min_inputs = []
        NSB_max_inputs = []
        NSB_on_inputs = []
        NSB_off_inputs = []
        st.markdown('Enter Information for Night Setback (NSB) of Temperature (Zone 1)')
        col8, col9, col10, col11, col12 = st.columns(5)
        NSB = col8.checkbox(label='NSB on', value=True, key=f'NSB_1')
        NSB_min = col9.number_input(label='Lower Bound [°C]', step=1, value=13, key='NSB_min_1')
        NSB_max = col10.number_input(label='Upper Bound [°C]', step=1, value=20, key='NSB_max_1')
        NSB_on = col11.number_input(label='Time NSB On [h]', step=1, value=22, min_value=0, max_value=24,
                                    key='NSB_on_1')
        NSB_off = col12.number_input(label='Time NSB Off [h]', step=1, value=7, min_value=0, max_value=24,
                                     key='NSB_off_1')
        NSB_inputs.append(NSB)
        NSB_min_inputs.append(NSB_min)
        NSB_max_inputs.append(NSB_max)
        NSB_on_inputs.append(NSB_on)
        NSB_off_inputs.append(NSB_off)
        if submitbutton or num_floors > 1:
            # Generate the NSB input fields dynamically
            for floor in range(1, num_floors):
                st.markdown(f'Enter Information for Night Setback (NSB) of Temperature (Zone {floor + 1})')
                col8, col9, col10, col11, col12 = st.columns(5)
                NSB = col8.checkbox(label='NSB on', value=True, key=f'NSB_{floor + 1}')
                NSB_min = col9.number_input(label='Lower Bound [°C]', step=1, value=13, key=f'NSB_min_{floor + 1}')
                NSB_max = col10.number_input(label='Upper Bound [°C]', step=1, value=20, key=f'NSB_max_{floor + 1}')
                NSB_on = col11.number_input(label='Time NSB On [h]', step=1, value=22, min_value=0, max_value=24,
                                            key=f'NSB_on_{floor + 1}')
                NSB_off = col12.number_input(label='Time NSB Off [h]', step=1, value=7, min_value=0, max_value=24,
                                             key=f'NSB_off_{floor + 1}')
                NSB_inputs.append(NSB)
                NSB_min_inputs.append(NSB_min)
                NSB_max_inputs.append(NSB_max)
                NSB_on_inputs.append(NSB_on)
                NSB_off_inputs.append(NSB_off)

        st.subheader('Simulation Settings')

        # New time frame input
        col1, col2 = st.columns(2)
        d1 = dt.date(2022, 1, 1)
        d2 = dt.date(2022, 12, 31)
        d_yesterday = dt.date.today() - dt.timedelta(days=1)
        sim_start = col1.date_input(label='Simulation Start Date', value=d1)  # min value of data set / weather data?
        sim_stop = col2.date_input(label='Simulation End Date', value=d2, max_value=d_yesterday)  # max value?

        # Data discretizaion in simulation time frame

        slider_options = np.around(np.concatenate((np.arange(0.05, 1, 0.05), np.arange(1, 13, 1))), 2)
        slider_options2 = ['3min', '6min', '12min', '15min', '30min', '1h', '2h', '3h', '4h', '5h', '6h', '8h', '12h']
        time_dt = st.select_slider("Data Time Step Discretization [h]", options=slider_options2, value='1h')

        # time_dt = col1.number_input(label = 'Time series discretization [Hours]', step = 0.1, value = 1, min_value= 0.1, max_value= 12)

        st.markdown('Select one of the following Weather Data APIs:')
        st.markdown('- Deutscher Wetterdienst (DWD) exclusively works for locations in Germany')
        st.markdown('- Visualcrossing can be used for global locations')

        weather_api = st.selectbox(label='Weather API Selection',
                                   options=weather_apilist, )  # label_visibility = 'hidden'

        # info text
        st.subheader('Chosen Inputs')
        st.markdown('Record of Chosen Inputs. To refresh press "Show Input Variables"')
        # Log inputs, so program simulates with the chosen input variables
        submit1 = st.form_submit_button('Log Input Variables',
                                        help='This button logs the chosen input variables and visualizes them')

        if submit1:
            # Visualize choosen Location
            col1, col2 = st.columns(2)
            location = pd.DataFrame(np.array([[float(lat), float(lon)]]), columns=['lat', 'lon'])
            loc = col1.map(location)

            # Visualize Building Parameter inputs
            data = {'BldStd': ['unsaniert', 'WSchV 95', 'EnEV 2009', 'EnEV 2014', 'GEG', 'KN45', 'KN30'],
                    'dStor': ['30', '25', '20', '20', '20', '20', '20'],
                    'dInsu': ['1', '5', '11.2', '11.2', '13.3', '22.3', '26']}
            df_bldstd = pd.DataFrame(data)
            df_bldstd = df_bldstd.set_index('BldStd')
            lst_bld = ['- Length of Building: {:.0f} m'.format(l), '- Width of Building: {:.0f} m'.format(b),
                       '- Height of Building: {:.0f} m'.format(h),
                       '- Number of Floors: {:.0f}'.format(num_floors), '- Window to Wall Ratios',
                       '  - North: {:.0f} %'.format(wtw[0] * 100), '  - East: {:.0f} %'.format(wtw[1] * 100),
                       '  - South: {:.0f} %'.format(wtw[2] * 100), '  - West: {:.0f} %'.format(wtw[3] * 100),
                       '- Building Standard: {}'.format(bldstd),
                       '  - Storage material thickness: {} cm'.format(df_bldstd.at[bldstd, 'dStor']),
                       '  - Insulation Material Thickness {} cm'.format(df_bldstd.at[bldstd, 'dInsu'])]
            s_bld = ''
            s_bld += " " + 'Building Parameters:' + "\n\n"
            for i in lst_bld:
                s_bld += i + "\n"

            col2.markdown(s_bld)

            col1, col2 = st.columns(2)

            # Visualize Temperature settings
            for floor in range(num_floors):
                s_temp = ''
                s_temp += " " + f'Target Temperatures Zone {floor + 1}' + "\n\n"
                col1.markdown(s_temp)
                hour = [1] * 24
                for i in range(24):
                    hour[i] = i
                lst_tempmin = [20] * 24
                lst_tempmax = [20] * 24
                for i in range(24):
                    lst_tempmin[i] = temp_min_inputs[floor]
                    lst_tempmax[i] = temp_max_inputs[floor]
                    if NSB_inputs[floor] == True and (i >= NSB_on_inputs[floor] or i <= NSB_off_inputs[floor]):  # night
                        lst_tempmin[i] = NSB_min_inputs[floor]
                        lst_tempmax[i] = NSB_max_inputs[floor]
                df_temp = pd.DataFrame({'Hour': hour,
                                        'Lower': lst_tempmin,
                                        'Upper': lst_tempmax})
                chart_colors = ['blue', 'red']
                chart = alt.Chart(df_temp).transform_fold(
                    ['Lower', 'Upper']
                ).mark_line().encode(
                    x=alt.X('Hour:O', axis=alt.Axis(labelAngle=0)),
                    y=alt.Y('value:Q', title='Temperature [°C]'),
                    color=alt.Color('key:N', legend=alt.Legend(orient='right'), title=None,
                                    scale=alt.Scale(range=chart_colors))
                )
                col1.altair_chart(chart, use_container_width=True)

            # Visualize Simulation parameters
            lst_simu = ['Simulation Start Date: {sim_start}'.format(sim_start=sim_start),
                        'Simulation End Date {sim_stop}'.format(sim_stop=sim_stop),
                        'Discretization: {time_dt}'.format(time_dt=time_dt),
                        'Weather API: {weather_api}'.format(weather_api=weather_api)]
            s_simu = ''
            s_simu += " " + 'Simulation Parameters:' + "\n\n"
            for i in lst_simu:
                s_simu += "- " + i + "\n"
            col2.markdown(s_simu)

# Start Simulation Button
simulated = 0
GUI1 = st.button('Start Simulation', help='This button starts the simulation with the logged variables', key='2')
if GUI1:
    # Send input variables to simulation program and get results
    df_all, zones, T_Amb, step_datetime, Q_Wlli_absRadsh = main.submit(bldstd, num_floors, l, h, lat, b,
                                                                       occupants_inputs, act_day_range, act_day_lower,
                                                                       act_day_upper, act_night_range, act_night_lower,
                                                                       act_night_upper, act_night_start, act_night_end,
                                                                       lon, sim_start, sim_stop, wtw, temp_min_inputs,
                                                                       temp_max_inputs, NSB_inputs, NSB_min_inputs,
                                                                       NSB_max_inputs, NSB_on_inputs, NSB_off_inputs,
                                                                       time_dt, weather_api)

    # Edit Dataframe for intended purposes
    floor_nr = 1
    for df in df_all:
        floor_nr_str = str(floor_nr)
        df = df[[0, 1, 2, 3, 4, 6, 7]]  # removes column with index 5
        df.columns = ['Luftaustauschverluste', 'interne Wärmegewinne', 'berechnete Heizlast',
                      'konvektive Wärmeübertragung Außenwand -> Fenster',
                      'konvektive Wärmeübertragung Außenwand -> Innenraum', 'berechnete Kühllast', 'Solare Gewinne']
        df = df.reset_index()
        df['index'] = df['index'].astype(str, errors='raise')
        df['index'] = df['index'].apply(lambda x: dt.datetime.strptime(x, '%Y-%m-%d %H:%M:%S'))
        df_all[floor_nr - 1] = df.copy()
        floor_nr += 1

    # Filter df for the right step size >1H
    if time_dt in ["3min", "6min", "12min", "30min", "1h"]:
        int_step = 1
    elif time_dt == "2h":
        int_step = 2
    elif time_dt == "3h":
        int_step = 3
    elif time_dt == "4h":
        int_step = 4
    elif time_dt == "5h":
        int_step = 5
    elif time_dt == "6h":
        int_step = 6
    elif time_dt == "8h":
        int_step = 8
    elif time_dt == "12h":
        int_step = 12
    T_Amb = pd.DataFrame(T_Amb)
    T_Amb = T_Amb.iloc[::int_step, :]
    floor_nr = 1
    for df in df_all:
        floor_nr_str = str(floor_nr)
        df = df.iloc[::int_step, :]
        df.columns = ['time_values', 'air_exchange_losses_values', 'internal_heat_gains_values', 'heating_load_values',
                      'window_values', 'wall_values', 'cooling_load_values',
                      'solar_heat_gains_values']  # keys for all the values including time are determined here
        df_all[floor_nr - 1] = df.copy()
        df_all[floor_nr - 1].to_csv(f"heatload_floor_{floor_nr_str}.csv", index=False)
        if floor_nr == 1:
            Building_HL = df.copy()
        if floor_nr > 1:
            Building_HL[
                ['air_exchange_losses_values', 'internal_heat_gains_values', 'heating_load_values', 'window_values',
                 'wall_values', 'cooling_load_values', 'solar_heat_gains_values']] = Building_HL[
                ['air_exchange_losses_values', 'internal_heat_gains_values', 'heating_load_values', 'window_values',
                 'wall_values', 'cooling_load_values', 'solar_heat_gains_values']].add(df[['air_exchange_losses_values',
                                                                                           'internal_heat_gains_values',
                                                                                           'heating_load_values',
                                                                                           'window_values',
                                                                                           'wall_values',
                                                                                           'cooling_load_values',
                                                                                           'solar_heat_gains_values']],
                                                                                       fill_value=0)
        floor_nr = floor_nr + 1
    Building_HL.to_csv("heatload_building.csv", index=False)

    if time_dt in ["1h", "2h", "3h", "4h", "5h", "6h", "8h",
                   "12h"]:  # creating a multiplicator to compansate for the timestep
        multiplicator = 1
    elif time_dt == "30min":
        multiplicator = 0.5
    elif time_dt == "15min":
        multiplicator = 0.25
    elif time_dt == "12min":
        multiplicator = 0.2
    elif time_dt == "6min":
        multiplicator = 0.1
    elif time_dt == "3min":
        multiplicator = 0.05

    T_veri = {
        "temperature": list(T_Amb["temperature"].values)}  # used to be T_Amb_dict, needed for plots of temperature

    simulated = 1
    with open("simulated_check.json", "w") as file:
        json.dump(simulated, file)
    with st.expander('Simulation Results', expanded=True):

        csv_to_json()
        st.sidebar.markdown("Main page")

        header = st.container()
        dataset = st.container()
        features = st.container()
        modelTraining = st.container()

        options = st.container()

        # a = open('heatload_floor_1.json')
        # b = open('san_data.json')

        st.subheader("Summary: Heating and Cooling Load")

        lin_data = df_all[0].copy()
        time_values = lin_data["time_values"].astype(str).tolist()

        date_data = pd.to_datetime(lin_data["time_values"]).tolist()
        date_data_dict_2 = dict()
        date_data_dict_6 = dict()
        for i in range(len(date_data)):
            date_data_dict_2[date_data[i].strftime("%Y") + ' ' + date_data[i].strftime("%b")] = []
        for i in range(len(date_data)):
            date_data_dict_2[date_data[i].strftime("%Y") + ' ' + date_data[i].strftime("%b")].append(
                Building_HL["heating_load_values"][i])

        for i in range(len(date_data)):
            date_data_dict_6[date_data[i].strftime("%Y") + ' ' + date_data[i].strftime("%b")] = []
        for i in range(len(date_data)):
            date_data_dict_6[date_data[i].strftime("%Y") + ' ' + date_data[i].strftime("%b")].append(
                Building_HL["cooling_load_values"][i])

        listkeys = list(date_data_dict_2.keys())

        plot_data_2 = [[]] * len(listkeys)
        for i in range(len(listkeys)):
            plot_data_2[i] = np.multiply(
                np.round(np.divide(np.sum(np.abs(date_data_dict_2[listkeys[i]])), 1000), decimals=2), multiplicator)

        plot_data_6 = [[]] * len(listkeys)
        for i in range(len(listkeys)):
            plot_data_6[i] = np.multiply(
                np.round(np.divide(np.sum(np.abs(date_data_dict_6[listkeys[i]])), 1000), decimals=2), multiplicator)

        Placeholder1 = [sum(plot_data_6[:i + 1]) + sum(plot_data_2[:i + 1]) for i in
                        range(len(plot_data_2))]  # This placeholder is used in the waterfall chart
        Placeholder = (np.abs(Placeholder1))
        Placeholder2 = list(Placeholder)

        options = {
            "title": {
                "text": f'Monthly rundown of Heating and Cooling Load - Building'
            },
            "tooltip": {
                "dataZoom": {"yAxisIndex": "true"},
                "trigger": 'axis',
                "axisPointer": {
                    "type": 'shadow'
                }
            },
            "legend": {
                "top": '7%',
                "left": 'center'
            },
            "grid": {
                "left": '3%',
                "right": '4%',
                "bottom": '3%',
                "containLabel": "true"
            },
            "xAxis": {
                "type": 'value'
            },
            "yAxis": {
                "type": 'category',
                "data": listkeys
            },
            "series": [
                {
                    "name": 'Heating Load [kWh]',
                    "type": 'bar',
                    "stack": 'total',
                    "label": {
                        "show": "true"
                    },
                    "emphasis": {
                        "focus": 'series'
                    },
                    "itemStyle": {
                        "color": "#FF4747"
                    },
                    "data": plot_data_2
                },
                {
                    "name": 'Cooling Load [kWh]',
                    "type": 'bar',
                    "stack": 'total',
                    "label": {
                        "show": "true"
                    },
                    "emphasis": {
                        "focus": 'series'
                    },
                    "itemStyle": {
                        "color": "#478BFF"
                    },
                    "data": plot_data_6
                }
            ]
        }
        st_echarts(options=options)

        options = {
            "title": {
                "text": ""
            },
            "tooltip": {
                "dataZoom": {"yAxisIndex": "true"},
                "trigger": 'axis',
                "axisPointer": {
                    "type": 'shadow'
                },
            },
            "legend": {
                "data": ['Heating Load [W]', 'Cooling Load [W]']
            },
            "grid": {
                "left": '3%',
                "right": '4%',
                "bottom": '3%',
                "containLabel": "true"
            },
            "xAxis": {
                "type": 'category',
                "data": listkeys
            },
            "yAxis": {
                "type": 'value'
            },
            "series": [
                {
                    "name": 'Placeholder',
                    "type": 'bar',
                    "stack": 'Total',
                    "silent": 'true',
                    "label": {
                        "show": "false",
                        "color": 'transparent'
                    },
                    "itemStyle": {
                        "borderColor": 'transparent',
                        "color": 'transparent'
                    },
                    "emphasis": {
                        "itemStyle": {
                            "borderColor": 'transparent',
                            "color": 'transparent'
                        }
                    },
                    "data": Placeholder1
                },
                {
                    "name": 'Heating Load [Wh]',
                    "type": 'bar',
                    "stack": 'Total',
                    "label": {
                        "show": "true",
                        "position": 'top'
                    },
                    "itemStyle": {
                        "color": "#FF4747"
                    },
                    "data": plot_data_2
                },
                {
                    "name": 'Cooling Load [Wh]',
                    "type": 'bar',
                    "stack": 'Total',
                    "label": {
                        "show": "true",
                        "position": 'bottom'
                    },
                    "itemStyle": {
                        "color": "#478BFF"
                    },
                    "data": plot_data_6
                }
            ]
        }

        st_echarts(options=options)

        if num_floors > 1:
            for z in range(num_floors - 1, -1, -1):
                zonenr = str(z + 1)
                # lin_data = pd.read_csv(f"heatload_floor_{zonenr}.csv")
                lin_data = df_all[z].copy()
                time_values = lin_data["time_values"].astype(str).tolist()
                # san_data = json.load(b)

                # arr = np.array([1, 2, 3, 4, 5, 6, 7, 8])
                # Heizlast = np.array(lin_data["heating_load_values"])
                # Kuhllast = np.array(lin_data["cooling_load_values"])

                # data = df_all[z].copy()
                date_data = pd.to_datetime(lin_data["time_values"]).tolist()
                date_data_dict_2 = dict()
                date_data_dict_6 = dict()
                for i in range(len(date_data)):
                    date_data_dict_2[date_data[i].strftime("%Y") + ' ' + date_data[i].strftime("%b")] = []
                for i in range(len(date_data)):
                    date_data_dict_2[date_data[i].strftime("%Y") + ' ' + date_data[i].strftime("%b")].append(
                        lin_data["heating_load_values"][i])

                for i in range(len(date_data)):
                    date_data_dict_6[date_data[i].strftime("%Y") + ' ' + date_data[i].strftime("%b")] = []
                for i in range(len(date_data)):
                    date_data_dict_6[date_data[i].strftime("%Y") + ' ' + date_data[i].strftime("%b")].append(
                        lin_data["cooling_load_values"][i])

                listkeys = list(date_data_dict_2.keys())

                plot_data_2 = [[]] * len(listkeys)
                for i in range(len(listkeys)):
                    plot_data_2[i] = np.multiply(
                        np.round(np.divide(np.sum(np.abs(date_data_dict_2[listkeys[i]])), 1000), decimals=2),
                        multiplicator)

                plot_data_6 = [[]] * len(listkeys)
                for i in range(len(listkeys)):
                    plot_data_6[i] = np.multiply(
                        np.round(np.divide(np.sum(np.abs(date_data_dict_6[listkeys[i]])), 1000), decimals=2),
                        multiplicator)

                Placeholder1 = [sum(plot_data_6[:i + 1]) + sum(plot_data_2[:i + 1]) for i in
                                range(len(plot_data_2))]  # This placeholder is used in the waterfall chart
                Placeholder = (np.abs(Placeholder1))
                Placeholder2 = list(Placeholder)

                options = {
                    "title": {
                        "text": f'Monthly rundown of Heating and Cooling Load - {zones[z].type} (Zone {zonenr})'
                    },
                    "tooltip": {
                        "dataZoom": {"yAxisIndex": "true"},
                        "trigger": 'axis',
                        "axisPointer": {
                            "type": 'shadow'
                        }
                    },
                    "legend": {
                        "top": '7%',
                        "left": 'center'
                    },
                    "grid": {
                        "left": '3%',
                        "right": '4%',
                        "bottom": '3%',
                        "containLabel": "true"
                    },
                    "xAxis": {
                        "type": 'value'
                    },
                    "yAxis": {
                        "type": 'category',
                        "data": listkeys
                    },
                    "series": [
                        {
                            "name": 'Heating Load [kWh]',
                            "type": 'bar',
                            "stack": 'total',
                            "label": {
                                "show": "true"
                            },
                            "emphasis": {
                                "focus": 'series'
                            },
                            "itemStyle": {
                                "color": "#FF4747"
                            },
                            "data": plot_data_2
                        },
                        {
                            "name": 'Cooling Load [kWh]',
                            "type": 'bar',
                            "stack": 'total',
                            "label": {
                                "show": "true"
                            },
                            "emphasis": {
                                "focus": 'series'
                            },
                            "itemStyle": {
                                "color": "#478BFF"
                            },
                            "data": plot_data_6
                        }
                    ]
                }
                st_echarts(options=options)

                options = {
                    "title": {
                        "text": ""
                    },
                    "tooltip": {
                        "dataZoom": {"yAxisIndex": "true"},
                        "trigger": 'axis',
                        "axisPointer": {
                            "type": 'shadow'
                        },
                    },
                    "legend": {
                        "data": ['Heating Load [W]', 'Cooling Load [W]']
                    },
                    "grid": {
                        "left": '3%',
                        "right": '4%',
                        "bottom": '3%',
                        "containLabel": "true"
                    },
                    "xAxis": {
                        "type": 'category',
                        "data": listkeys
                    },
                    "yAxis": {
                        "type": 'value'
                    },
                    "series": [
                        {
                            "name": 'Placeholder',
                            "type": 'bar',
                            "stack": 'Total',
                            "silent": 'true',
                            "label": {
                                "show": "false",
                                "color": 'transparent'
                            },
                            "itemStyle": {
                                "borderColor": 'transparent',
                                "color": 'transparent'
                            },
                            "emphasis": {
                                "itemStyle": {
                                    "borderColor": 'transparent',
                                    "color": 'transparent'
                                }
                            },
                            "data": Placeholder1
                        },
                        {
                            "name": 'Heating Load [Wh]',
                            "type": 'bar',
                            "stack": 'Total',
                            "label": {
                                "show": "true",
                                "position": 'top'
                            },
                            "itemStyle": {
                                "color": "#FF4747"
                            },
                            "data": plot_data_2
                        },
                        {
                            "name": 'Cooling Load [Wh]',
                            "type": 'bar',
                            "stack": 'Total',
                            "label": {
                                "show": "true",
                                "position": 'bottom'
                            },
                            "itemStyle": {
                                "color": "#478BFF"
                            },
                            "data": plot_data_6
                        }
                    ]
                }

                st_echarts(options=options)

        lin_data = df_all[0].copy()
        time_values = lin_data["time_values"].astype(str).tolist()

        options = {
            "title": {
                "text": f'Total Heating Load and Cooling Load compared - Building'
            },
            "tooltip": {
                "trigger": 'item'
            },
            "toolbox": {
                "feature": {
                    "dataZoom": {"yAxisIndex": "true"},
                    "dataView": {"show": "true", "readOnly": "false"},
                    "restore": {"show": "true"},
                    "saveAsImage": {"show": "true"}
                }
            },
            "legend": {
                "top": '8%',
                "left": 'center'
            },
            "grid": {
                "top": '11%',
            },
            "series": [
                {
                    "name": 'Heating vs Cooling Load',
                    "type": 'pie',
                    "radius": ['40%', '70%'],
                    "avoidLabelOverlap": "false",
                    "itemStyle": {
                        "borderRadius": 10,
                        "borderColor": '#fff',
                        "borderWidth": 2
                    },
                    "label": {
                        "show": "false",
                        "position": 'center'
                    },
                    "emphasis": {
                        "label": {
                            "show": "true",
                            "fontSize": 40,
                            "fontWeight": 'bold'
                        }
                    },
                    "labelLine": {
                        "show": "false"
                    },
                    "data": [
                        {'value': np.multiply(
                            np.round(np.divide(np.sum(np.abs(Building_HL["heating_load_values"])), 1000000),
                                     decimals=2), multiplicator), 'name': 'Heating Load [MWh]',
                            "itemStyle": {"color": "#FF4747"}},
                        {'value': np.multiply(
                            np.round(np.divide(np.sum(np.abs(Building_HL["cooling_load_values"])), 1000000),
                                     decimals=2), multiplicator), 'name': 'Cooling Load [MWh]',
                            "itemStyle": {"color": "#478BFF"}},
                    ]
                }
            ]
        }
        st_echarts(options=options)

        if num_floors > 1:
            for z in range(num_floors - 1, -1, -1):
                zonenr = str(z + 1)
                lin_data = df_all[z].copy()
                time_values = lin_data["time_values"].astype(str).tolist()

                options = {
                    "title": {
                        "text": f'Total Heating Load and Cooling Load compared - {zones[z].type} (Zone {zonenr})'
                    },
                    "tooltip": {
                        "trigger": 'item'
                    },
                    "toolbox": {
                        "feature": {
                            "dataZoom": {"yAxisIndex": "true"},
                            "dataView": {"show": "true", "readOnly": "false"},
                            "restore": {"show": "true"},
                            "saveAsImage": {"show": "true"}
                        }
                    },
                    "legend": {
                        "top": '8%',
                        "left": 'center'
                    },
                    "grid": {
                        "top": '11%',
                    },
                    "series": [
                        {
                            "name": 'Heating vs Cooling Load',
                            "type": 'pie',
                            "radius": ['40%', '70%'],
                            "avoidLabelOverlap": "false",
                            "itemStyle": {
                                "borderRadius": 10,
                                "borderColor": '#fff',
                                "borderWidth": 2
                            },
                            "label": {
                                "show": "false",
                                "position": 'center'
                            },
                            "emphasis": {
                                "label": {
                                    "show": "true",
                                    "fontSize": 40,
                                    "fontWeight": 'bold'
                                }
                            },
                            "labelLine": {
                                "show": "false"
                            },
                            "data": [
                                {'value': np.multiply(
                                    np.round(np.divide(np.sum(np.abs(lin_data["heating_load_values"])), 1000000),
                                             decimals=2), multiplicator), 'name': 'Heating Load [MWh]',
                                    "itemStyle": {"color": "#FF4747"}},
                                {'value': np.multiply(
                                    np.round(np.divide(np.sum(np.abs(lin_data["cooling_load_values"])), 1000000),
                                             decimals=2), multiplicator), 'name': 'Cooling Load [MWh]',
                                    "itemStyle": {"color": "#478BFF"}},
                            ]
                        }
                    ]
                }
                st_echarts(options=options)

            # Other possiblities at: https://echarts.apache.org/examples/en/index.html

        st.subheader("Details")
        st.subheader("Building")
        lin_data = df_all[0].copy()
        time_values = lin_data["time_values"].astype(str).tolist()

        colors = ['#FF4747', '#478BFF', '#FFA047', '#37b3ae', '#b3a037', '#249109', '#e6f02b', '#000000'];
        options = {
            "color": colors,
            "tooltip": {
                "trigger": 'axis',
                "axisPointer": {
                    "type": 'cross'
                }
            },
            "grid": {
                "right": '5%',
                "top": '25%'
            },
            "toolbox": {
                "feature": {
                    "dataZoom": {"yAxisIndex": "true"},
                    "dataView": {"show": "true", "readOnly": "false"},
                    "restore": {"show": "true"},
                    "saveAsImage": {"show": "true"}
                }
            },
            "legend": {
                "data": [
                    'Heating Load [W]',
                    'Cooling Load [W]',
                    'Heat Exchange Inner Space -> Window [W]',
                    'Heat Exchange Inner Space -> Outter Wall [W]',
                    'Air Exchange Losses [W]',
                    'Internal Heat Gains [W]',
                    'Solar Heat Gains [W]'
                ]
            },
            "xAxis": [
                {
                    "type": 'category',
                    "axisTick": {
                        "alignWithLabel": "true"
                    },
                    "data": time_values
                }
            ],
            "yAxis": [
                {
                    "type": 'value',
                    "name": 'Heat Exchange [W]',
                    "position": 'right',
                    "alignTicks": "true",
                    "offset": 0,
                    "axisLine": {
                        "show": "true",
                        "lineStyle": {
                            "color": colors[7]
                        }
                    },
                    "axisLabel": {
                        "formatter": '{value} W'
                    }
                }
            ],
            "series": [
                {
                    "name": 'Heating Load [W]',
                    "type": 'line',
                    "yAxisIndex": 0,
                    "data": Building_HL["heating_load_values"].tolist()
                },
                {
                    "name": 'Cooling Load [W]',
                    "type": 'line',
                    "yAxisIndex": 0,
                    "data": Building_HL["cooling_load_values"].tolist()
                },
                {
                    "name": 'Heat Exchange Inner Space -> Window [W]',
                    "type": 'bar',
                    "stack": 'Total',
                    "yAxisIndex": 0,
                    "data": Building_HL["window_values"].tolist()
                },
                {
                    "name": 'Heat Exchange Inner Space -> Outter Wall [W]',
                    "type": 'bar',
                    "stack": 'Total',
                    "yAxisIndex": 0,
                    "data": Building_HL["wall_values"].tolist()
                },
                {
                    "name": 'Air Exchange Losses [W]',
                    "type": 'bar',
                    "stack": 'Total',
                    "yAxisIndex": 0,
                    "data": Building_HL["air_exchange_losses_values"].tolist()
                },
                {
                    "name": 'Internal Heat Gains [W]',
                    "type": 'bar',
                    "stack": 'Total',
                    "yAxisIndex": 0,
                    "data": Building_HL["internal_heat_gains_values"].tolist()
                },
                {
                    "name": 'Solar Heat Gains [W]',
                    "type": 'bar',
                    "stack": 'Total',
                    "yAxisIndex": 0,
                    "data": Building_HL["solar_heat_gains_values"].tolist()
                }
            ]
        }
        st_echarts(options=options)

        if num_floors > 1:
            for z in range(num_floors - 1, -1, -1):
                zonenr = str(z + 1)
                lin_data = df_all[z].copy()
                time_values = lin_data["time_values"].astype(str).tolist()

                st.subheader(f'{zones[z].type} (Zone {zonenr})')

                colors = ['#FF4747', '#478BFF', '#FFA047', '#37b3ae', '#b3a037', '#249109', '#e6f02b', '#000000'];
                options = {
                    "color": colors,
                    "tooltip": {
                        "trigger": 'axis',
                        "axisPointer": {
                            "type": 'cross'
                        }
                    },
                    "grid": {
                        "right": '5%',
                        "top": '25%'
                    },
                    "toolbox": {
                        "feature": {
                            "dataZoom": {"yAxisIndex": "true"},
                            "dataView": {"show": "true", "readOnly": "false"},
                            "restore": {"show": "true"},
                            "saveAsImage": {"show": "true"}
                        }
                    },
                    "legend": {
                        "data": [
                            'Heating Load [W]',
                            'Cooling Load [W]',
                            'Heat Exchange Inner Space -> Window [W]',
                            'Heat Exchange Inner Space -> Outter Wall [W]',
                            'Air Exchange Losses [W]',
                            'Internal Heat Gains [W]',
                            'Solar Heat Gains [W]'
                        ]
                    },
                    "xAxis": [
                        {
                            "type": 'category',
                            "axisTick": {
                                "alignWithLabel": "true"
                            },
                            "data": time_values
                        }
                    ],
                    "yAxis": [
                        {
                            "type": 'value',
                            "name": 'Heat Exchange [W]',
                            "position": 'right',
                            "alignTicks": "true",
                            "offset": 0,
                            "axisLine": {
                                "show": "true",
                                "lineStyle": {
                                    "color": colors[7]
                                }
                            },
                            "axisLabel": {
                                "formatter": '{value} W'
                            }
                        }
                    ],
                    "series": [
                        {
                            "name": 'Heating Load [W]',
                            "type": 'line',
                            "yAxisIndex": 0,
                            "data": lin_data["heating_load_values"].tolist()
                        },
                        {
                            "name": 'Cooling Load [W]',
                            "type": 'line',
                            "yAxisIndex": 0,
                            "data": lin_data["cooling_load_values"].tolist()
                        },
                        {
                            "name": 'Heat Exchange Inner Space -> Window [W]',
                            "type": 'bar',
                            "stack": 'Total',
                            "yAxisIndex": 0,
                            "data": lin_data["window_values"].tolist()
                        },
                        {
                            "name": 'Heat Exchange Inner Space -> Outter Wall [W]',
                            "type": 'bar',
                            "stack": 'Total',
                            "yAxisIndex": 0,
                            "data": lin_data["wall_values"].tolist()
                        },
                        {
                            "name": 'Air Exchange Losses [W]',
                            "type": 'bar',
                            "stack": 'Total',
                            "yAxisIndex": 0,
                            "data": lin_data["air_exchange_losses_values"].tolist()
                        },
                        {
                            "name": 'Internal Heat Gains [W]',
                            "type": 'bar',
                            "stack": 'Total',
                            "yAxisIndex": 0,
                            "data": lin_data["internal_heat_gains_values"].tolist()
                        },
                        {
                            "name": 'Solar Heat Gains [W]',
                            "type": 'bar',
                            "stack": 'Total',
                            "yAxisIndex": 0,
                            "data": lin_data["solar_heat_gains_values"].tolist()
                        }
                    ]
                }
                st_echarts(options=options)

        lin_data = df_all[0].copy()
        time_values = lin_data["time_values"].astype(str).tolist()

        colors = ['#b3a037', '#249109', '#d68f1c', '#e6f02b', '#000000'];
        options = {
            "title": {
                "text": 'Building'
            },
            "color": colors,
            "tooltip": {
                "trigger": 'axis',
                "axisPointer": {
                    "type": 'cross'
                }
            },
            "grid": {
                "right": '5%'
            },
            "toolbox": {
                "feature": {
                    "dataZoom": {"yAxisIndex": "true"},
                    "dataView": {"show": "true", "readOnly": "false"},
                    "restore": {"show": "true"},
                    "saveAsImage": {"show": "true"}
                }
            },
            "legend": {
                "data": [
                    'Air Exchange Losses [W]',
                    'Internal Heat Gains [W]',
                    'Temperature[°C]',
                    'Solar Heat Gains [W]'
                ]
            },
            "xAxis": [
                {
                    "type": 'category',
                    "axisTick": {
                        "alignWithLabel": "true"
                    },
                    "data": time_values
                }
            ],
            "yAxis": [
                {
                    "type": 'value',
                    "name": 'Losses and Gains [W]',
                    "position": 'right',
                    "alignTicks": "true",
                    "axisLine": {
                        "show": "true",
                        "lineStyle": {
                            "color": colors[4]
                        }
                    },
                    "axisLabel": {
                        "formatter": '{value} W'
                    }
                },
                {
                    "type": 'value',
                    "name": 'Temperature',
                    "position": 'left',
                    "alignTicks": "true",
                    "axisLine": {
                        "show": "true",
                        "lineStyle": {
                            "color": colors[2]
                        }
                    },
                    "axisLabel": {
                        "formatter": '{value} °C'
                    }
                }
            ],
            "series": [
                {
                    "name": 'Air Exchange Losses [W]',
                    "type": 'line',
                    "yAxisIndex": 0,
                    "data": Building_HL["air_exchange_losses_values"].tolist()
                },
                {
                    "name": 'Internal Heat Gains [W]',
                    "type": 'line',
                    "yAxisIndex": 0,
                    "data": Building_HL["internal_heat_gains_values"].tolist()
                },
                {
                    "name": 'Temperature',
                    "type": 'line',
                    "yAxisIndex": 1,
                    "data": T_veri["temperature"]
                },
                {
                    "name": 'Solar Heat Gains [W]',
                    "type": 'line',
                    "yAxisIndex": 0,
                    "data": Building_HL["solar_heat_gains_values"].tolist()
                }
            ]
        }
        st_echarts(options=options)

        if num_floors > 1:
            for z in range(num_floors - 1, -1, -1):
                zonenr = str(z + 1)
                lin_data = df_all[z].copy()
                time_values = lin_data["time_values"].astype(str).tolist()

                colors = ['#b3a037', '#249109', '#d68f1c', '#e6f02b', '#000000'];
                options = {
                    "title": {
                        "text": f'{zones[z].type} - (Zone {zonenr})'
                    },
                    "color": colors,
                    "tooltip": {
                        "trigger": 'axis',
                        "axisPointer": {
                            "type": 'cross'
                        }
                    },
                    "grid": {
                        "right": '5%'
                    },
                    "toolbox": {
                        "feature": {
                            "dataZoom": {"yAxisIndex": "true"},
                            "dataView": {"show": "true", "readOnly": "false"},
                            "restore": {"show": "true"},
                            "saveAsImage": {"show": "true"}
                        }
                    },
                    "legend": {
                        "data": [
                            'Air Exchange Losses [W]',
                            'Internal Heat Gains [W]',
                            'Temperature[°C]',
                            'Solar Heat Gains [W]'
                        ]
                    },
                    "xAxis": [
                        {
                            "type": 'category',
                            "axisTick": {
                                "alignWithLabel": "true"
                            },
                            "data": time_values
                        }
                    ],
                    "yAxis": [
                        {
                            "type": 'value',
                            "name": 'Losses and Gains [W]',
                            "position": 'right',
                            "alignTicks": "true",
                            "axisLine": {
                                "show": "true",
                                "lineStyle": {
                                    "color": colors[4]
                                }
                            },
                            "axisLabel": {
                                "formatter": '{value} W'
                            }
                        },
                        {
                            "type": 'value',
                            "name": 'Temperature',
                            "position": 'left',
                            "alignTicks": "true",
                            "axisLine": {
                                "show": "true",
                                "lineStyle": {
                                    "color": colors[2]
                                }
                            },
                            "axisLabel": {
                                "formatter": '{value} °C'
                            }
                        }
                    ],
                    "series": [
                        {
                            "name": 'Air Exchange Losses [W]',
                            "type": 'line',
                            "yAxisIndex": 0,
                            "data": lin_data["air_exchange_losses_values"].tolist()
                        },
                        {
                            "name": 'Internal Heat Gains [W]',
                            "type": 'line',
                            "yAxisIndex": 0,
                            "data": lin_data["internal_heat_gains_values"].tolist()
                        },
                        {
                            "name": 'Temperature',
                            "type": 'line',
                            "yAxisIndex": 1,
                            "data": T_veri["temperature"]
                        },
                        {
                            "name": 'Solar Heat Gains [W]',
                            "type": 'line',
                            "yAxisIndex": 0,
                            "data": lin_data["solar_heat_gains_values"].tolist()
                        }
                    ]
                }
                st_echarts(options=options)

        st.subheader(f"Energy Flows Between the Outer Surfaces and the Exterior Space")
        st.subheader(f"Building")
        lin_data = df_all[0].copy()
        time_values = lin_data["time_values"].astype(str).tolist()

        for z in range(num_floors):
            if z == 0:
                Q_Amb_WlleCnv_sum = np.multiply(np.sum(zones[z].Q_Amb_WlleCnv, axis=0), multiplicator)
                Q_Amb_WlleRadln_sum = np.multiply(np.sum(zones[z].Q_Amb_WlleRadln, axis=0), multiplicator)
                Q_Amb_WlleRadsh_sum = np.multiply(np.sum(zones[z].Q_Amb_WlleRadsh, axis=0), multiplicator)

                Q_Amb_WndeCnv_sum = np.multiply(np.sum(zones[z].Q_Amb_WndeCnv, axis=0), multiplicator)
                Q_Amb_WndeRadln_sum = np.multiply(np.sum(zones[z].Q_Amb_WndeRadln, axis=0), multiplicator)
                Q_Amb_WndeRadsh_sum = np.multiply(np.sum(zones[z].Q_Amb_WndeRadsh, axis=0), multiplicator)
            if z > 0:
                Q_Amb_WlleCnv_sum += np.multiply(np.sum(zones[z].Q_Amb_WlleCnv, axis=0), multiplicator)
                Q_Amb_WlleRadln_sum += np.multiply(np.sum(zones[z].Q_Amb_WlleRadln, axis=0), multiplicator)
                Q_Amb_WlleRadsh_sum += np.multiply(np.sum(zones[z].Q_Amb_WlleRadsh, axis=0), multiplicator)

                Q_Amb_WndeCnv_sum += np.multiply(np.sum(zones[z].Q_Amb_WndeCnv, axis=0), multiplicator)
                Q_Amb_WndeRadln_sum += np.multiply(np.sum(zones[z].Q_Amb_WndeRadln, axis=0), multiplicator)
                Q_Amb_WndeRadsh_sum += np.multiply(np.sum(zones[z].Q_Amb_WndeRadsh, axis=0), multiplicator)

        # Bottom-Floor and Top-Ceiling are the boundaries of building
        Q_Amb_WlleCnv_sum[4] = np.multiply(np.sum(zones[0].Q_Amb_WlleCnv[:, 4], axis=0), multiplicator)
        Q_Amb_WlleCnv_sum[5] = np.multiply(np.sum(zones[num_floors - 1].Q_Amb_WlleCnv[:, 5], axis=0), multiplicator)

        nodelist = [Q_Amb_WlleCnv_sum, Q_Amb_WlleRadln_sum, Q_Amb_WlleRadsh_sum, Q_Amb_WndeCnv_sum, Q_Amb_WndeRadln_sum,
                    Q_Amb_WndeRadsh_sum]
        walls = ["North Wall", "East Wall", "South Wall", "West Wall", "Floor", "Ceiling"]
        windows = ["North Window", "East Window", "South Window", "West Window"]

        energy_flows = {
            "nodes": [
                {"name": "Convective Gains"},
                {"name": "Long Wave gains"},
                {"name": "Short Wave Gains (Sunlight)"},
                {"name": "North Wall"},
                {"name": "East Wall"},
                {"name": "South Wall"},
                {"name": "West Wall"},
                {"name": "Floor"},
                {"name": "Ceiling"},
                {"name": "North Window"},
                {"name": "East Window"},
                {"name": "South Window"},
                {"name": "West Window"},
                {"name": "Convective Losses"},
                {"name": "Long Wave Losses"},
                {"name": "Short Wave losses"}
            ],
            "links": []}

        for i in range(len(Q_Amb_WlleCnv_sum)):
            if Q_Amb_WlleCnv_sum[i] > 0:
                energy_flows["links"].append(
                    {"source": "Convective Gains", "target": walls[i], "value": Q_Amb_WlleCnv_sum[i]})
            if Q_Amb_WlleCnv_sum[i] < 0:
                energy_flows["links"].append(
                    {"source": walls[i], "target": "Convective Losses", "value": np.abs(Q_Amb_WlleCnv_sum[i])})

        for i in range(len(Q_Amb_WlleRadln_sum)):
            if Q_Amb_WlleRadln_sum[i] > 0:
                energy_flows["links"].append(
                    {"source": "Long Wave Gains", "target": walls[i], "value": Q_Amb_WlleRadln_sum[i]})
            if Q_Amb_WlleRadln_sum[i] <= 0:
                energy_flows["links"].append(
                    {"source": walls[i], "target": "Long Wave Losses", "value": np.abs(Q_Amb_WlleRadln_sum[i])})

        for i in range(len(Q_Amb_WlleRadsh_sum)):
            if Q_Amb_WlleRadsh_sum[i] >= 0:
                energy_flows["links"].append(
                    {"source": "Short Wave Gains (Sunlight)", "target": walls[i], "value": Q_Amb_WlleRadsh_sum[i]})
            if Q_Amb_WlleRadsh_sum[i] < 0:
                energy_flows["links"].append(
                    {"source": walls[i], "target": "Short Wave Losses", "value": np.abs(Q_Amb_WlleRadsh_sum[i])})

        for i in range(len(Q_Amb_WndeCnv_sum)):
            if Q_Amb_WndeCnv_sum[i] > 0:
                energy_flows["links"].append(
                    {"source": "Convective Gains", "target": windows[i], "value": Q_Amb_WndeCnv_sum[i]})
            elif Q_Amb_WndeCnv_sum[i] < 0:
                energy_flows["links"].append(
                    {"source": windows[i], "target": "Convective Losses", "value": np.abs(Q_Amb_WndeCnv_sum[i])})

        for i in range(len(Q_Amb_WndeRadln_sum)):
            if Q_Amb_WndeRadln_sum[i] > 0:
                energy_flows["links"].append(
                    {"source": "Long Wave Gains", "target": windows[i], "value": Q_Amb_WndeRadln_sum[i]})
            elif Q_Amb_WndeRadln_sum[i] < 0:
                energy_flows["links"].append(
                    {"source": windows[i], "target": "Long Wave Losses", "value": np.abs(Q_Amb_WndeRadln_sum[i])})

        for i in range(len(Q_Amb_WndeRadsh_sum)):
            if Q_Amb_WndeRadsh_sum[i] > 0:
                energy_flows["links"].append(
                    {"source": "Short Wave Gains (Sunlight)", "target": windows[i], "value": Q_Amb_WndeRadsh_sum[i]})
            elif Q_Amb_WndeRadsh_sum[i] < 0:
                energy_flows["links"].append(
                    {"source": windows[i], "target": "Short Wave Losses", "value": np.abs(Q_Amb_WndeRadsh_sum[i])})

        unique_key = f"my_unique_key_Building"
        options = {
            "tooltip": {
                "trigger": 'item',
                "triggerOn": 'mousemove'
            },
            "series": [
                {
                    "type": 'sankey',
                    "data": energy_flows["nodes"],
                    "links": energy_flows["links"],
                    "emphasis": {
                        "focus": 'adjacency'
                    },
                    "lineStyle": {
                        "color": 'gradient',
                        "curveness": 0.5
                    }
                }
            ]
        }
        st_echarts(options=options, key=unique_key)

        if num_floors > 1:
            for z in range(num_floors - 1, -1, -1):
                zonenr = str(z + 1)
                lin_data = df_all[z].copy()
                time_values = lin_data["time_values"].astype(str).tolist()
                st.subheader(f"{zones[z].type} (Zone {zonenr})")

                Q_Amb_WlleCnv_sum = np.multiply(np.sum(zones[z].Q_Amb_WlleCnv, axis=0), multiplicator)
                Q_Amb_WlleRadln_sum = np.multiply(np.sum(zones[z].Q_Amb_WlleRadln, axis=0), multiplicator)
                Q_Amb_WlleRadsh_sum = np.multiply(np.sum(zones[z].Q_Amb_WlleRadsh, axis=0), multiplicator)

                Q_Amb_WndeCnv_sum = np.multiply(np.sum(zones[z].Q_Amb_WndeCnv, axis=0), multiplicator)
                Q_Amb_WndeRadln_sum = np.multiply(np.sum(zones[z].Q_Amb_WndeRadln, axis=0), multiplicator)
                Q_Amb_WndeRadsh_sum = np.multiply(np.sum(zones[z].Q_Amb_WndeRadsh, axis=0), multiplicator)

                nodelist = [Q_Amb_WlleCnv_sum, Q_Amb_WlleRadln_sum, Q_Amb_WlleRadsh_sum, Q_Amb_WndeCnv_sum,
                            Q_Amb_WndeRadln_sum, Q_Amb_WndeRadsh_sum]
                walls = ["North Wall", "East Wall", "South Wall", "West Wall", "Floor", "Ceiling"]
                windows = ["North Window", "East Window", "South Window", "West Window"]

                energy_flows = {
                    "nodes": [
                        {"name": "Convective Gains"},
                        {"name": "Long Wave gains"},
                        {"name": "Short Wave Gains (Sunlight)"},
                        {"name": "North Wall"},
                        {"name": "East Wall"},
                        {"name": "South Wall"},
                        {"name": "West Wall"},
                        {"name": "Floor"},
                        {"name": "Ceiling"},
                        {"name": "North Window"},
                        {"name": "East Window"},
                        {"name": "South Window"},
                        {"name": "West Window"},
                        {"name": "Convective Losses"},
                        {"name": "Long Wave Losses"},
                        {"name": "Short Wave losses"}
                    ],
                    "links": []}

                for i in range(len(Q_Amb_WlleCnv_sum)):
                    if Q_Amb_WlleCnv_sum[i] > 0:
                        energy_flows["links"].append(
                            {"source": "Convective Gains", "target": walls[i], "value": Q_Amb_WlleCnv_sum[i]})
                    if Q_Amb_WlleCnv_sum[i] < 0:
                        energy_flows["links"].append(
                            {"source": walls[i], "target": "Convective Losses", "value": np.abs(Q_Amb_WlleCnv_sum[i])})

                for i in range(len(Q_Amb_WlleRadln_sum)):
                    if Q_Amb_WlleRadln_sum[i] > 0:
                        energy_flows["links"].append(
                            {"source": "Long Wave Gains", "target": walls[i], "value": Q_Amb_WlleRadln_sum[i]})
                    if Q_Amb_WlleRadln_sum[i] <= 0:
                        energy_flows["links"].append(
                            {"source": walls[i], "target": "Long Wave Losses", "value": np.abs(Q_Amb_WlleRadln_sum[i])})

                for i in range(len(Q_Amb_WlleRadsh_sum)):
                    if Q_Amb_WlleRadsh_sum[i] >= 0:
                        energy_flows["links"].append({"source": "Short Wave Gains (Sunlight)", "target": walls[i],
                                                      "value": Q_Amb_WlleRadsh_sum[i]})
                    if Q_Amb_WlleRadsh_sum[i] < 0:
                        energy_flows["links"].append({"source": walls[i], "target": "Short Wave Losses",
                                                      "value": np.abs(Q_Amb_WlleRadsh_sum[i])})

                for i in range(len(Q_Amb_WndeCnv_sum)):
                    if Q_Amb_WndeCnv_sum[i] > 0:
                        energy_flows["links"].append(
                            {"source": "Convective Gains", "target": windows[i], "value": Q_Amb_WndeCnv_sum[i]})
                    elif Q_Amb_WndeCnv_sum[i] < 0:
                        energy_flows["links"].append({"source": windows[i], "target": "Convective Losses",
                                                      "value": np.abs(Q_Amb_WndeCnv_sum[i])})

                for i in range(len(Q_Amb_WndeRadln_sum)):
                    if Q_Amb_WndeRadln_sum[i] > 0:
                        energy_flows["links"].append(
                            {"source": "Long Wave Gains", "target": windows[i], "value": Q_Amb_WndeRadln_sum[i]})
                    elif Q_Amb_WndeRadln_sum[i] < 0:
                        energy_flows["links"].append({"source": windows[i], "target": "Long Wave Losses",
                                                      "value": np.abs(Q_Amb_WndeRadln_sum[i])})

                for i in range(len(Q_Amb_WndeRadsh_sum)):
                    if Q_Amb_WndeRadsh_sum[i] > 0:
                        energy_flows["links"].append({"source": "Short Wave Gains (Sunlight)", "target": windows[i],
                                                      "value": Q_Amb_WndeRadsh_sum[i]})
                    elif Q_Amb_WndeRadsh_sum[i] < 0:
                        energy_flows["links"].append({"source": windows[i], "target": "Short Wave Losses",
                                                      "value": np.abs(Q_Amb_WndeRadsh_sum[i])})

                unique_key = f"my_unique_key_{zonenr}"
                options = {
                    "tooltip": {
                        "trigger": 'item',
                        "triggerOn": 'mousemove'
                    },
                    "series": [
                        {
                            "type": 'sankey',
                            "data": energy_flows["nodes"],
                            "links": energy_flows["links"],
                            "emphasis": {
                                "focus": 'adjacency'
                            },
                            "lineStyle": {
                                "color": 'gradient',
                                "curveness": 0.5
                            }
                        }
                    ]
                }
                st_echarts(options=options, key=unique_key)

            ###Preliminary Sankey for future implementation of multi zone model
            # st.subheader("Suggestions for the Multiroom Model")

            # options = {
            # "tooltip": {
            #    "trigger": 'item',
            #    "triggerOn": 'mousemove'
            # },
            # "series": [
            #    {
            #    "type": 'sankey',
            #    "data": san_data["nodes"],
            #    "links": san_data["links"],
            #    "emphasis": {
            #        "focus": 'adjacency'
            #    },
            #    "lineStyle": {
            #        "color": 'gradient',
            #        "curveness": 0.5
            #    }
            #    }
            # ]
            # };
            # st_echarts(options=options)
simulated_check = "simulated_check.json"
if submitbutton or submit1:
    if os.path.exists(simulated_check):
        os.remove(simulated_check)
    else:
        print("File does not exist")

# Check, ob Datei bereits vorhanden ist; Datei ueberprueft ob Simulation schon durchgefuehrt wurde
if os.path.exists(simulated_check):
    try:
        with open("simulated_check.json", "r") as file:
            sim = json.load(file)
        if sim == 1:
            with st.expander('Download Thermal Load Profiles as CSV', expanded=True):
                for x in range(num_floors):
                    unique_key = f"my_unique_key_{str(x + 1)}"


                    def create_download_button(filename, text, unique_key):
                        with open(filename, 'rb') as f:
                            button = st.download_button(
                                label=text,
                                data=f,
                                file_name=filename,
                                mime='text/csv',
                                key=unique_key
                            )
                        return button


                    # Download-Button anzeigen
                    create_download_button(f'heatload_floor_{str(x + 1)}.csv', f'Download Floor {str(x + 1)}',
                                           unique_key)
                create_download_button('heatload_building.csv', 'Download Building', "my_unique_key_building")
    except OSError as e:
        print(f"Error: {e}")
