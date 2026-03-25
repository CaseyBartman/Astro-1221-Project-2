"""
Centralized constants for the project
"""

# -------------- Astronomical calculation constants --------------
# RA ranges best viewed at midnight during these seasons -> See this source https://in-the-sky.org/data/ra_season.php?town=4509177
# Taking Fall as an example: The source states that the RAs of 0-6 are best for Sep to Oct to Nov, so we set that range there
SEASON_RA = {
    'Spring': (12, 16),
    'Summer': (16, 0), # Wraps from 16 -> 24 -> 0
    'Fall':   (0, 6),
    'Winter': (6, 12)
}

# Mapping of RA hour to best viewing month. Again, grabbed from the above source
MONTH_MAP = {
    0: "September",
    1: "October",
    2: "November",
    3: "December",
    4: "January",
    5: "February",
    6: "March",
    7: "April",
    8: "May",
    9: "June",
    10: "July",
    11: "August"
}
# RA bounds and mapping
RA_MIN_HOUR = 0
RA_MAX_HOUR = 24
MONTHS_IN_YEAR = 12

# Each month represents this many RA hours (24 / 12 = 2)
RA_TO_MONTH_BUCKET_SIZE = RA_MAX_HOUR / MONTHS_IN_YEAR

# Formula for limiting magnitude calculation:: m = 2.7 + 5 * log10(D)
MAG_BASE_CONSTANT = 2.7
MAG_LOG_COEFFICIENT = 5

# How much brighter than viewing tool limit -> Grabbed from this source:  http://www.icq.eps.harvard.edu/MagScale.html 
# IT IS IMPORTANT TO NOTE THAT THE MAX MAGNITUDE OF ANY MESSIER OBJECT IS LESS THAN 13. So, this "telescope by aperture" 
# requirement doesn't apply as well as listing the tools that we could use, since a telescope could give views for each of the objects. This is a bit more dynamic.
NAKED_EYE_BRIGHT_URBAN_VISIBILITY_THRESHOLD = 3.0
NAKED_EYE_SUBURBAN_RURAL_DARK_VISIBILITY_THRESHOLD = 5.0
BINOCULAR_VISIBILITY_THRESHOLD = 8.5


# Classifying size of objects:
LARGE_OBJECT_APPARENT_SIZE_LIMIT = 60
VERY_LARGE_OBJECT_APPARENT_SIZE_LIMIT = 20
MEDIUM_OBJECT_APPARENT_SIZE_LIMIT = 5

# Default telescope aperture (mm)
DEFAULT_APERTURE_MM = 114


# -------------- Messier Catalog Constants --------------
CSV_URL = "https://raw.githubusercontent.com/7468696e6b/fourmilab-hplanet/master/Messier.csv"
CSV_FILENAME = "messier_catalog.csv"
LOG_FILENAME = "logged_objects_for_grading/messier_objects_log.txt"
DEFAULT_APERTURE_LOG_FILENAME = "logged_objects_for_grading/filtered_objects_default_aperture.txt"
CUSTOM_APERTURE_LOG_FILENAME = "logged_objects_for_grading/filtered_objects_custom_aperture.txt"


# Column names for Messier catalog CSV
COLUMNS = {
    'NAME': 'Name',
    'NGC': 'NGC',
    'CONSTELLATION': 'Constellation',
    'TYPE': 'Class',
    'RA': 'Right ascension',
    'DEC': 'Declination',
    'MAGNITUDE': 'Magnitude',
    'ANGULAR_SIZE': 'Angular size',
    'BURNHAM': 'Burnham',
    'REMARKS': 'Remarks',
}
