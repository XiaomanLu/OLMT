import os
from .paths import *

def site_location(site):
    if site in ['z6_SEEED', 'SEEED']:
        site_lat, site_lon = 35.9716431, -83.9047674
    elif site in ['z6-20662-Melshouse', 'VictorAshe-2']:
        site_lat, site_lon = 35.9836745, -83.9928031
    elif site in ['z6-Chilhowee', 'WestView']:
        site_lat, site_lon = 35.9660326, -83.9612832
    elif site in ['z6-Cumberland', 'Cumberland']:
        site_lat, site_lon = 35.9886325, -84.0155383
    elif site in ['z6-Victor_Ashe', 'VictorAshe']:
        site_lat, site_lon = 35.9829284, -83.9926842    
    elif site in ['z6-WestHills', 'WestHills']:
        site_lat, site_lon = 35.9316965, -84.0445624    
    return(site_lat, site_lon+360)


# 'WestView' doesn't have enough data
SITE_LIST = ['VictorAshe', 'SEEED', 'Cumberland', 'WestHills']

OBS_FILES = {
    'VictorAshe': os.path.join(PATH_DATA, 'observations', '20250116',
                              'z6-Victor_Ashe(z6-20661)-Configuration 2-1737057276.2937331.csv'),
    'SEEED': os.path.join(PATH_DATA, 'observations', '20250116',
                          'z6_SEEED(z6-20751)-Configuration 5-1738767817.596226.csv'),
    'Cumberland': os.path.join(PATH_DATA, 'observations', '20250116',
                             'z6-Cumberland(z6-20657)-Configuration 3-1737057264.8158581.csv'),
    'WestView': os.path.join(PATH_DATA, 'observations', '20250116',
                            'z6-Chilhowee(z6-20749)-Configuration 6-1737057277.4213405.csv'),
    'WestHills': os.path.join(PATH_DATA, 'observations', '20250116',
                             'z6-WestHills(z6-20478)-Configuration 3-1737057286.3159492.csv'),
    # soil moisture-only file
    'VictorAshe-2': os.path.join(PATH_DATA, 'observations', '20250116',
                                'z6-20662-Melshouse(z6-20662)-Configuration 6-1737057256.328495.csv'),
    'Cumberland-2': os.path.join(PATH_DATA, 'observations', '20250116',
                                'z6-Cumberland_soil(z6-20483)-Configuration 2-1738770741.7317216.csv'),
}# The old westview sensor does not have any data
# 'WestView-1': 'z6-West_View_Park(z6-20750)-Configuration 6-1733437844.1557636.csv', 

OBS_PREFIX = {
        'VictorAshe': 'z6-Victor_Ashe', 
        'SEEED': 'z6_SEEED', 
        'Cumberland': 'z6-Cumberland', 
        'WestView': 'z6-Chilhowee', 
        'VictorAshe-2': 'z6-20662-Melshouse',
        'WestHills': 'z6-WestHills',
        'WestView-1': 'z6-West_View_Park'
}


SITE_SHORTNAME = {
    'VictorAshe': 'VA',
    'SEEED': 'SD', 
    'Cumberland': 'CL', 
    'WestHills': 'WH'
}


site_plotID_dict = {
    'VictorAshe': 0, 
    'SEEED': 1, 
    'Cumberland': 2, 
    'WestHills': 3   
}


# make sure to use the same units for all the variables!
OBS_ATTRS = {
    'P': ('Precipitation', 'mm/hour'),
    'WS': ('Wind speed', 'm/s'),
    'TA': ('Air temperature', '$^o$C'),
    'PA': ('Air pressure', 'Pa'),
    'VPD': ('Vapor pressure deficit', 'Pa'),
    'SW': ('Downwelling shortwave', 'W/m2'),
    'LW': ('Downwelling longwave', 'W/m2'),
    'PAR': ('Photosynthetically active radiation', 'µmol_m-2_s-1 PPFD')
}

# forcing variables to ELM
FORC_VARS = ['P', 'WS', 'TA', 'PA', 'SW', 'LW', 'VPD']

