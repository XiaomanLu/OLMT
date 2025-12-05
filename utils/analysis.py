import pandas as pd
import os
import xarray as xr
import numpy as np
import math
from utils.paths import *
from utils.constants import *

# PATH_ELM_OUT = '/Users/x5l/ORNL Dropbox/Xiaoman Lu/Oak_Research_Materials/Project3_Urban/Codes_Urban/test_lux/check_output/e3sm_run/'
# PATH_DATA = "/Users/x5l/ORNL Dropbox/Xiaoman Lu/Oak_Research_Materials/Project3_Urban/Analysis/data/"

def get_e3sm_flist(datestamp, site_name, aggr, year_range, suffix='', mypath=PATH_ELM_OUT):
    """Get the list of E3SM files

    Args:
        site_name (str): SEEED, etc. 
        aggr (str): either "col" or "pft"
        year_range (iterable): list of years to use

    Returns:
        list: list of E3SM file paths
    """

    if aggr == "col":
        h = "h0"
    else:
        h = "h1"          
    
    return [
        os.path.join(
            mypath,      
            suffix,
            f"{datestamp}_{site_name}_ICB20TRCNPRDCTCBC",
            "run",
            f"{datestamp}_{site_name}_ICB20TRCNPRDCTCBC.elm.{h}.{year}-01-01-00000.nc",
        )
        for year in year_range
    ]


## to show ensemble analysis result
def get_e3sm_flist_ensemble(datestamp, site_name, aggr, year_range, suffix='', mypath=PATH_ELM_OUT):
    if aggr == "col":
        h = "h0"
    else:
        h = "h1"            
    
    return [
        os.path.join(
            mypath,  
            "UQ",   
            suffix,
            f"{datestamp}_{site_name}_ICB20TRCNPRDCTCBC",
            "g04000",    #one example       
            f"{datestamp}_{site_name}_ICB20TRCNPRDCTCBC.elm.{h}.{year}-01-01-00000.nc",
        )
        for year in year_range
    ]


def get_e3sm_flist_treatment(datestamp, site_name, aggr, year_range, treatment, suffix='', mypath=PATH_ELM_OUT):
    """Get the list of E3SM files

    Args:
        site_name (str): SEEED, etc. 
        aggr (str): either "col" or "pft"
        year_range (iterable): list of years to use

    Returns:
        list: list of E3SM file paths
    """

    if aggr == "col":
        h = "h0"
    else:
        h = "h1"            
    
    return [
        os.path.join(
            mypath,        
            suffix,
            f"{datestamp}_{site_name}_ICB20TRCNPRDCTCBC_{treatment}",
            "run",
            f"{datestamp}_{site_name}_ICB20TRCNPRDCTCBC_{treatment}.elm.{h}.{year}-01-01-00000.nc",
        )
        for year in year_range
    ]


def get_e3sm_col_data(col_var, flist):
    # fmt:off
    LEVGRND = np.array([0.007100635, 0.027925, 0.06225858, 0.1188651, 0.2121934,
                        0.3660658, 0.6197585, 1.038027, 1.727635, 2.864607, 4.739157,
                        7.829766, 12.92532, 21.32647, 35.17762])
    LEVGRND_I = np.append(np.insert(
        (LEVGRND[1:] + LEVGRND[:-1])*0.5, 0, 0
    ), LEVGRND[-1] + 0.5 * (LEVGRND[-1] - LEVGRND[-2]))
    # fmt: on
    THICKNESS = np.diff(LEVGRND_I)

    if col_var == 'VPD':
        site_name = flist[0].split('/')[-1].split('_')[1]
        data = pd.read_csv(os.path.join(PATH_DATA, 'ERA5_Land', f'Downscaled_{site_name}.csv'), 
                           index_col = 0, header = 0, parse_dates = True)
        year_start = int(flist[0].split('/')[-1].split('.')[-2].split('-')[0])
        year_end = int(flist[0].split('/')[-1].split('.')[-2].split('-')[0])
        data = data.loc[(data.index.year >= year_start) & (data.index.year <= year_end), 'VPD']

        collect = {}

        # annual time series
        collect['ts_annual'] = data.resample("1Y").mean()

        # monthly time series
        collect['ts_monthly'] = data.resample("1M").mean()

        # daily time series
        collect['ts_daily'] = data.resample("1D").mean()

        # annual cycle (365 days)
        collect['annual_cycle'] = data.groupby(data.index.dayofyear).mean()

        return collect, 'Pa'
    
    hr = xr.open_mfdataset(flist)    
    if col_var in  ["TSA", "TBOT"]:
        data = hr[col_var] - 273.15
        unit = "degC"
    elif col_var == "P":
        data = (hr["RAIN"] + hr["SNOW"].values) * 86400
        unit = "mm/day"
    elif col_var == "ET":
        data = (hr["QVEGE"] + hr["QVEGT"] + hr["QSOIL"].values) * 86400
        unit = "mm/day"
    elif col_var == "PAR":
        data = hr['FSDS'] * 0.435
        unit = "W/m2"
    elif col_var == "SW":
        data = hr['FSDS']
        unit = "W/m2"
    elif col_var == "SM15":
        data = (
            hr["H2OSOI"][:, 0, :] * THICKNESS[0]
            + hr["H2OSOI"][:, 1, :] * THICKNESS[1]
            + hr["H2OSOI"][:, 2, :] * THICKNESS[2]
            + hr["H2OSOI"][:, 3, :] * (0.15 - LEVGRND_I[3])            
        ) / 0.15
        unit = "mm3/mm3"    
    elif col_var == "SM10": 
        data = (
            hr["H2OSOI"][:, 0, :] * THICKNESS[0]
            + hr["H2OSOI"][:, 1, :] * THICKNESS[1]
            + hr["H2OSOI"][:, 2, :] * THICKNESS[2]
            + hr["H2OSOI"][:, 3, :] * (0.10 - LEVGRND_I[3])            
        ) / 0.10
        unit = "mm3/mm3"        
    elif col_var == "TSOIL15":
        data = (
            hr["TSOI"][:, 0, :] * THICKNESS[0]
            + hr["TSOI"][:, 1, :] * THICKNESS[1]
            + hr["TSOI"][:, 2, :] * THICKNESS[2]
            + hr["TSOI"][:, 3, :] * (0.15 - LEVGRND_I[3])
        ) / 0.15 - 273.15
        unit = "degC"
    elif col_var == "TSOIL10":
        data = (
            hr["TSOI"][:, 0, :] * THICKNESS[0]
            + hr["TSOI"][:, 1, :] * THICKNESS[1]
            + hr["TSOI"][:, 2, :] * THICKNESS[2]
            + hr["TSOI"][:, 3, :] * (0.10 - LEVGRND_I[3])
        ) / 0.10 - 273.15
        unit = "degC"
    else:
        data = hr[col_var]
        unit = hr[col_var].attrs["units"]
        if unit.endswith("/s"):
            data = data * 86400
            unit = unit.replace("/s", "/day")
    
    datetime_list = pd.DatetimeIndex([pd.to_datetime(str(date)) for date in data['time'].values])
    if data.shape[1] == 1:
        data = pd.Series(data.values[:, 0], index = datetime_list)
    else:
        data = pd.DataFrame(data.values, index = datetime_list)

    collect = {}

    # annual time series
    collect['ts_annual'] = data.resample("1Y").mean()

    # monthly time series
    collect['ts_monthly'] = data.resample("1M").mean()

    # daily time series
    collect['ts_daily'] = data.resample("1D").mean()

    # annual cycle (365 days)
    collect['annual_cycle'] = data.groupby(data.index.dayofyear).mean()

    # diurnal cycle (separately for each month)
    collect['diurnal_cycle'] = data.groupby(data.index.month).apply(lambda dfa: dfa.groupby(dfa.index.hour).mean())

    hr.close()
    return (collect, unit)


def get_e3sm_pft_data(col_var, pft, flist):       
    hr = xr.open_mfdataset(flist)
    data = hr[col_var].sel(pft=pft)                  
    unit = hr[col_var].attrs["units"]
    
    if unit.endswith("/s"):
        data = data * 86400
        unit = unit.replace("/s", "/day")
        
    datetime_list = pd.DatetimeIndex([pd.to_datetime(str(date)) for date in data['time'].values])    
    data = pd.DataFrame(data.values, index = datetime_list)

    collect = {}

    # annual time series
    collect['ts_annual'] = data.resample("1Y").mean()

    # monthly time series
    collect['ts_monthly'] = data.resample("1M").mean()

    # daily time series
    collect['ts_daily'] = data.resample("1D").mean()

    # annual cycle (365 days)
    collect['annual_cycle'] = data.groupby(data.index.dayofyear).mean()

    # diurnal cycle (separately for each month)
    collect['diurnal_cycle'] = data.groupby(data.index.month).apply(lambda dfa: dfa.groupby(dfa.index.hour).mean())

    hr.close()
    return (collect, unit)


def get_obs_var(site_name, varname, datestamp, style = ["ts_daily", "diurnal_cycle"]):
    VAR_STRING = {
        "TSA": " degree_C Air Temperature",
        "TBOT": " degree_C Air Temperature",
        "P": " mm Precipitation",
        "SM15": " m3/m3 Water Content",
        "SM10": " m3/m3 Water Content",
        "TSOIL15": " degree_C Soil Temperature",
        "TSOIL10": " degree_C Soil Temperature",
        "FIRE": " W/m2 Emitted Long Wave", # "emitted infrared (longwave) radiation", W/m2
        "VPD": " kPa VPD",
        "PAR": " µmol_m-2_s-1 PPFD",
        "SW": " W/m2 Incident Short Wave"
    }
    #   "FSA": " W/m² Net Radiation", # FSA is absorbed solar radiation in ELM; not comparable

    if not varname in VAR_STRING.keys():
        raise Exception("Not implemented")

    colname = VAR_STRING[varname]

    if datestamp == "20231005":
        filename = os.path.join(PATH_OBS, f"{site_name}_{datestamp}.csv")
    elif datestamp == "20240107":
        filemap = {
            'SEEED': 'z6_SEEED(z6-20751)-Configuration 5-1704649507.9922347.csv', 
            'Melshouse': 'z6-20662-Melshouse(z6-20662)-Configuration 3-1704649507.9958599.csv',
            'Chilhowee': 'z6-Chilhowee(z6-0749)-Configuration 3-1704649512.9286878.csv', 
            'Cumberland': 'z6-Cumberland(z6-20657)-Configuration 3-1704649517.0280929.csv', 
            'VictorAshe': 'z6-Victor_Ashe(z6-20661)-Configuration 2-1704649518.247449.csv', 
            'WestView': 'z6-West_View_Park(z6-20750)-Configuration 4-1704649524.1238825.csv', 
            'WestHills': 'z6-WestHills(z6-20478)-Configuration 3-1704649524.3132195.csv'
        }
        filename = os.path.join(PATH_DATA, 'observations', '20240107', filemap[site_name])
    elif datestamp == "20241205":
        filemap = {
            'VictorAshe': 'z6-Victor_Ashe(z6-20661)-Configuration 2-1733437795.1125717.csv', 
            'SEEED': 'z6_SEEED(z6-20751)-Configuration 5-1733437800.0522914.csv', 
            'Cumberland': 'z6-Cumberland(z6-20657)-Configuration 3-1733437826.030838.csv', 
            'WestView': 'z6-Chilhowee(z6-20749)-Configuration 4-1733437824.9572446.csv', 
            #'VictorAshe-2': 'z6-20662-Melshouse(z6-20662)-Configuration 6-1733437806.0274708.csv',
            'WestHills': 'z6-WestHills(z6-20478)-Configuration 3-1733437846.646373.csv'
        }
        filename = os.path.join(PATH_DATA, 'observations', '20241205', filemap[site_name])        
    elif datestamp == "20250116": 
        filemap = {
           'VictorAshe': 'z6-Victor_Ashe(z6-20661)-Configuration 2-1737057276.2937331.csv',
           'SEEED': 'z6_SEEED(z6-20751)-Configuration 5-1738767817.596226.csv',
           'Cumberland': 'z6-Cumberland(z6-20657)-Configuration 3-1737057264.8158581.csv',
           'WestView':  'z6-Chilhowee(z6-20749)-Configuration 6-1737057277.4213405.csv',
           'WestHills': 'z6-WestHills(z6-20478)-Configuration 3-1737057286.3159492.csv',
            # soil moisture-only file
           'VictorAshe-2': 'z6-20662-Melshouse(z6-20662)-Configuration 6-1737057256.328495.csv',
           'Cumberland-2': 'z6-Cumberland_soil(z6-20483)-Configuration 2-1738770741.7317216.csv'
        }
        if site_name in ['VictorAshe','Cumberland'] and varname in ['SM15','SM10','TSOIL10','TSOIL15']:
            filename = os.path.join(PATH_DATA, 'observations', '20250116', filemap[site_name + '-2'])
        else:
            filename = os.path.join(PATH_DATA, 'observations', '20250116', filemap[site_name])              
    else:
        raise Exception("datestamp is not implemented")        
            
    data = pd.read_csv(
        filename,
        index_col=0,
        header=0,
        skiprows=2,
        parse_dates=True,
    )

    # average over multiple observations    
    match_col = [colname in c for c in data.columns]    
    data = data.loc[:, match_col].mean(axis=1)

    # remove bad periods
    if site_name == 'VictorAshe':
        data = data.loc[data.index >= pd.to_datetime('2023-07-15 00:00:00')]
        if varname == 'P':
            data.loc[data.index < pd.Timestamp('2024-06-20')] = np.nan
        elif varname in ['SW','PAR']:
            data.loc[data.index < pd.Timestamp('2024-02-16')] = np.nan
    elif site_name == 'Cumberland':
        if varname == 'SW':
            data.loc[data.index < pd.Timestamp('2024-04-01')] = np.nan
        elif varname == "PAR":
            data.loc[data.index < pd.Timestamp('2024-02-16')] = np.nan

    # remove 2/29 for compatibility with model calendar
    data = data.loc[(data.index.month != 2) | (data.index.day != 29)]

    if varname == "PAR":
        # umol m-2 s-1 convert to W/m2 
        data = data * (1e-6 * 220000)
    if varname == "VPD":
        # kPa to Pa
        data = data * 1e3

    if style == "ts_daily":
        if varname == "P":
            # mm per 15 min intervals is converted to mm/day
            data = data.resample('1D').agg({'value': lambda x: np.nan if x.isna().all() else x.sum()})
        else:
            data = data.resample('1D').agg({'value': lambda x: np.nan if x.isna().all() else x.mean()})
    elif style == "diurnal_cycle":
        # Cut off by 2023 end of year
        data = data.loc[data.index < pd.to_datetime('2023-12-31 23:00:00'), :]

        # Resample to 1 hour
        data = data.resample('1H').mean()

        # Apply monthly average
        data = data.groupby(data.index.month).apply(lambda dfa: dfa.groupby(data.index.hour).mean())

    return data


def read_obs(site_name):
    """ Read site observations. 
        Output dataframe: day-hour by variable name """
    if site_name in ['Chilhowee', 'WestView']:
        print(f'Site {site_name} has too little data. Skipping...')
        return

    keymap = {
        'P': ['ATMOS 41 All-in-one Weather Station', ' mm Precipitation'],
        'WS': ['ATMOS 41 All-in-one Weather Station', ' m/s Wind Speed'],
        'TA': ['ATMOS 41 All-in-one Weather Station', ' degree_C Air Temperature'],
        'PA': ['ATMOS 41 All-in-one Weather Station', ' kPa Atmospheric Pressure'],
        'VPD': ['ATMOS 41 All-in-one Weather Station', ' kPa VPD'],
        'SW': ['SN-500 Apogee Net Radiometer', ' W/m2 Incident Short Wave'],
        'LW': ['SN-500 Apogee Net Radiometer', ' W/m2 Incident Long Wave'],
        'PAR': ['SQ-521 PAR Photon Flux', ' µmol_m-2_s-1 PPFD']
    }

    # Get dataframe
    #folder = filemap[site_name].split('.')[0].split('-')
    #folder = 'All-' + '-'.join(folder[:-2] + [folder[-1]])
    data = pd.read_csv(OBS_FILES[site_name], header = [1,2], index_col = 0, 
                       skiprows=0, parse_dates=True)      

    data = data[[v for _, v in keymap.items()]]
    data.columns = data.columns.droplevel(0)

    # Replace variable name
    data = data.rename({v[1]:k for k, v in keymap.items()}, axis = 1)

    # Adjust units
    data['VPD'] = data['VPD'].clip(lower = 0.) * 1000. # kPa -> Pa
    data['PA'] = data['PA'] * 1000. # kPa -> Pa
    ### data['TA'] = data['TA'] + 273.15 # degC -> Kelvin

    # Resample to 1 hour
    data = data.resample('1H').mean()

    # Precipitation unit is mm per 15 minute intervals
    data['P'] = data['P'] * 4 # convert to sum for precipitation

    # remove bad periods
    if site_name == 'VictorAshe':
        data = data.loc[data.index >= pd.to_datetime('2023-07-15 00:00:00'), :]
        data.loc[data.index < pd.Timestamp('2024-06-20'), 'P'] = np.nan
        data.loc[data.index < pd.Timestamp('2024-02-16'), 'SW'] = np.nan
        data.loc[data.index < pd.Timestamp('2024-02-16'), 'PAR'] = np.nan
    elif site_name == 'Cumberland':
        data.loc[data.index < pd.Timestamp('2024-04-01'), 'SW'] = np.nan
        data.loc[data.index < pd.Timestamp('2024-02-16'), 'PAR'] = np.nan

    # Make sure all days are included
    data = data.reindex(pd.date_range(data.index[0], data.index[-1] + pd.Timedelta(hours=1), 
                                      freq = '1H'))

    # Drop Feb 29
    data = data.loc[~((data.index.month == 2) & (data.index.day == 29)), :]

    return data



def calculate_vpd(q, T, P):
    """
    Calculate Vapor Pressure Deficit (VPD) from specific humidity, temperature, and atmospheric pressure.

    Parameters:
    q (float): Specific humidity (kg/kg)
    T (float): Temperature (°C)
    P (float): Atmospheric pressure (Pa)

    Returns:
    float: Vapor Pressure Deficit (Pa)
    """
    # Calculate saturation vapor pressure (es)
    es = 610.78 * math.exp((17.2694 * T) / (T + 237.3))   # Convert hPa to Pa

    # Calculate actual vapor pressure (e)
    e = (q / (0.622 + (0.378 * q))) * P

    # Calculate VPD
    vpd = max(0, (es - e))
    return vpd


def read_hrrr(site_name):
    ### read hrrr csv file
    data_f01 = []
    for year in range(2014, 2025):
        data_f01.append(
            pd.read_csv(os.path.join(PATH_DATA, 'hrrr_wrfsfcf01_at_sites', 
                                     f'HRRR-wrfsfcf01_at_sites_{year}.csv'),
                        index_col = [1,0], parse_dates = True)
        )
    data_f01 = pd.concat(data_f01, axis = 0)
    data_f01 = data_f01.loc[OBS_PREFIX[site_name], :]

    data_f00 = []
    for year in range(2014, 2025):
        data_f00.append(
            pd.read_csv(os.path.join(PATH_DATA, 'hrrr_wrfsfcf00_at_sites', 
                                     f'HRRR-wrfsfcf00_at_sites_{year}.csv'),
                        index_col = [1,0], parse_dates = True)
        )
    data_f00 = pd.concat(data_f00, axis = 0)
    data_f00 = data_f00.loc[OBS_PREFIX[site_name], :]

    ### use Prate from data_f01 and other variables from data_f00
    data_Prate = data_f01[['Prate']]
    # (need to shift back the time stamp 1 hour)
    data_Prate.index = data_Prate.index - pd.Timedelta(hours = 1)
    data_envs = data_f00.drop(columns=['Prate'])    
    data_Prate = data_Prate.reset_index().rename(columns={'time': 'time'})
    data_envs = data_envs.reset_index().rename(columns={'time': 'time'})
    data = pd.merge(data_Prate, data_envs, on='time', how='outer')
    data.set_index(['time'], inplace=True)
    data = data[~data.index.isnull()]       

    ### change variable names
    map_dict = {'Prate': 'P', 'PRES': 'PA', 
                'Uwind_10m': 'Uwind', 'Vwind_10m': 'Vwind',                
                'TMP_2m': 'TA',  'SPFH_2m': 'SPFH',                
                'DSWRF': 'SW', 'DLWRF': 'LW'}
    data = data.rename(map_dict, axis = 1)

    ### convert HRRR units to the same as the observation    
    # precipitation: kg/m2/s => mm/hour     
    data['P'] = data['P'] * 3600     
    # temperature: K => '$^o$C'
    data['TA'] = data['TA'] - 273.15

    ### calculate windspeed
    data['WS'] = np.sqrt(data['Uwind']**2 + data['Vwind']**2) #m/s

    ### calculate VPD   
    data['VPD'] = data.apply(lambda row: calculate_vpd(row['SPFH'], row['TA'], row['PA']), axis=1)

    # drop unnecessary columns
    data = data.drop(columns=['Uwind', 'Vwind', 'SPFH'])            

    # Check and remove duplicate indices
    data = data[~data.index.duplicated(keep='first')]

    # discard partial year
    data = data.loc[data.index.year > 2014, :].sort_index()

    # Convert datetime to local time (UTC -5)
    data.iloc[:-5, :] = data.iloc[5:, :].values
    data.iloc[-5:, :] = data.iloc[-29:-24, :].values # fill with 24 hours ago

    # Make sure all days are included
    data = data.reindex(pd.date_range('2015-01-01', data.index[-1], freq = '1H'))

    # Drop Feb 29
    data = data.loc[~((data.index.month == 2) & (data.index.day == 29)), :]

    # At the end, gap-fill invalid SW days with averages of previous & after days
    sw = data['SW'].copy()
    sw.loc[sw > 600] = sw.interpolate(method = 'linear').loc[sw > 600].values
    # some days have total zero SW
    npos = sw.groupby(sw.index.date).apply(lambda ds: len(np.where(ds > 1e-6)[0]))
    zero_days = npos.index[npos == 0]
    for date in zero_days:
        ### use the average of all the other years on the same date
        others = sw.loc[(sw.index.month == date.month) & (sw.index.day == date.day) & \
                        (sw.index.year != date.year)]
        others = others.groupby(others.index.hour).mean()
        sw.loc[(sw.index.year == date.year) & (sw.index.month == date.month) & \
               (sw.index.day == date.day)] = others.values
        ###print(date, others.values)
    data['SW'] = sw.values

    # appears to have Downwelling shortwave outlier in Cumberland????

    return data


def read_era5(name):
    # Get dataframe
    era5_data = pd.read_csv(os.path.join(PATH_OUT, 'bias_correct_era5_land', 
                                        f'Reprocessed_{name}.csv'),
                            index_col = 0, parse_dates = True)

    # Convert datetime to local time (UTC -5)
    temp = era5_data.iloc[:5].values
    era5_data.iloc[:-5] = era5_data.iloc[5:].values
    era5_data.iloc[-5:] = temp
    era5_data.index.name = 'time'

    # Precipitation unit is mm/hour
    # Air temperature to K
    era5_data['TA'] = era5_data['TA'] - 273.15

    # Drop Feb 29
    era5_data = era5_data.loc[~((era5_data.index.month == 2) & (era5_data.index.day == 29)), :]

    return era5_data


def read_hrrr_corrected(site_name):
    """ Read the bias-corrected HRRR result, which are from `bias_correct_hrrr_spline.py` 
        and `bias_correct_hrrr_P.py` """
    corrected = {}
    for var in ['P'] + FORC_VARS:
        corrected[var] = pd.read_csv(os.path.join(PATH_OUT, 'bias_correct_hrrr', site_name,
                                                  f'{var}_corrected.csv'), 
                                     index_col = 0, parse_dates = True).iloc[:, 0]
    corrected = pd.DataFrame(corrected)

    # Drop Feb 29
    corrected = corrected.loc[~((corrected.index.month == 2) & (corrected.index.day == 29)), :]

    return corrected


def noleap_doy(tvec):
    """ Obtain the day of year index as if all the years were non-leap (1-365)
    from a pandas.DatetimeIndex 
    """
    doy = tvec.dayofyear
    doy = np.where(
        (tvec.month >= 3) & (tvec.year % 4 == 0), 
        doy-1, doy
    )
    return doy


def summarize(y):
    """ Return daily time series and the month-by-diurnal cycle, 
        with month labels for the latter. 
    """
    y_daily = y.resample('1D').mean()
    y_diurnal = y.groupby(y.index.month).apply(lambda dfa: dfa.groupby(dfa.index.hour).mean())

    months = y_diurnal.index.get_level_values(0)[y_diurnal.index.get_level_values(1) == 0]
    locs = np.where(y_diurnal.index.get_level_values(1) == 0)[0]

    return y_daily, y_diurnal, months, locs


from scipy import stats
def mystats(x,y):
    '''
    return r, p, rmse   

    '''    
    x, y = x.ravel(), y.ravel()
    mask = np.isfinite(x) & np.isfinite(y)       
    # print("mask shape", mask.shape)  # Should match x.shape and y.shape
    # print("data shape", x.shape, y.shape)    
    
    x, y = x[mask], y[mask]       
    
    if len(x)>=3 and np.std(x)!=0 and np.std(y)!=0:    #std to ensure x or y is not constant values
        r, p_value = stats.pearsonr(x,y) #note: r*r is not equal to r2_score     
        rmse = np.sqrt(np.mean((x - y) ** 2))   
    else:
        r, p_value, rmse = np.nan, np.nan, np.nan    
    
    return(r, p_value, rmse)








