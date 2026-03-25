import pandas as pd
import numpy as np
import logging
from constants import (
    MONTH_MAP, COLUMNS, DEFAULT_APERTURE_MM,
    RA_MIN_HOUR, RA_MAX_HOUR, MONTHS_IN_YEAR,
    MAG_BASE_CONSTANT, MAG_LOG_COEFFICIENT,
    NAKED_EYE_BRIGHT_URBAN_VISIBILITY_THRESHOLD,
    NAKED_EYE_SUBURBAN_RURAL_DARK_VISIBILITY_THRESHOLD,
    BINOCULAR_VISIBILITY_THRESHOLD,
    RA_TO_MONTH_BUCKET_SIZE,
    SEASON_RA, 
    LARGE_OBJECT_APPARENT_SIZE_LIMIT,
    VERY_LARGE_OBJECT_APPARENT_SIZE_LIMIT,
    MEDIUM_OBJECT_APPARENT_SIZE_LIMIT,
)

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class AstroAnalyticsEngine:
    """
    Core analytics engine for Messier object data.

    Responsibilities:
    - Clean and normalize raw CSV data
    - Compute astronomical properties (RA, visibility, apparent size)
    - Provide simple query methods for API/LLM/UI layers
    """

    def __init__(self, data_list):
        self.df = pd.DataFrame(data_list)
        self.columns = COLUMNS
        self.default_aperture = DEFAULT_APERTURE_MM

    def clean_data(self):
        """
        Cleans and enriches dataset with derived columns:
        - RA in decimal form
        - Best viewing month
        - Normalized object type
        - Parsed angular size + categories
        """
        mag_col = self.columns['MAGNITUDE']
        ra_col = self.columns['RA']
        type_col = self.columns['TYPE']
        size_col = self.columns['ANGULAR_SIZE']

        # Convert magnitude to numeric (invalid → NaN)
        if mag_col in self.df.columns:
            self.df[mag_col] = pd.to_numeric(self.df[mag_col], errors='coerce')

        # Convert "5h 34.5m" → decimal hours
        if ra_col in self.df.columns:
            self.df['RA_Decimal'] = self.df[ra_col].apply(self.parse_ra_to_decimal)
            # Map RA → best viewing month
            self.df['BestViewingMonth'] = self.df[ra_col].apply(self.ra_to_month)

        # Converts messy strings into:
        # Galaxy / Nebula / Cluster / Other
        if type_col in self.df.columns:
            self.df['NormalizedType'] = self.df[type_col].apply(self.normalize_object_type)
            self.df['NormalizedType'] = pd.Categorical(self.df['NormalizedType'])

        # Angular size processing
        # Example raw values:
        # "6x4" → elliptical object
        # "10"  → circular object
        if size_col in self.df.columns:

            # Step 1: Parse string into tuple
            # "6x4" → (6,4)
            parsed = self.df[size_col].apply(self.parse_angular_size)

            # Step 2: Extract major axis
            self.df['AngularSizeMajor'] = parsed.apply(
                lambda x: x[0] if isinstance(x, tuple) else np.nan
            )

            # Step 3: Extract minor axis
            self.df['AngularSizeMinor'] = parsed.apply(
                lambda x: x[1] if isinstance(x, tuple) else np.nan
            )

            # Step 4: Compute average apparent size
            # This gives a single number for sorting/filtering
            self.df['ApparentSizeAvg'] = self.df[
                ['AngularSizeMajor', 'AngularSizeMinor']
            ].mean(axis=1)

            # Step 5: Convert to human-readable category
            self.df['SizeCategory'] = self.df['ApparentSizeAvg'].apply(self.classify_size)

        # Fill missing values consistently
        self.df.fillna(np.nan, inplace=True)

        logger.info("DATA_CLEAN_COMPLETE")


    def parse_ra_to_decimal(self, ra_value):
        """Convert RA string to decimal hours."""
        if pd.isna(ra_value):
            return np.nan
        try:
            parts = str(ra_value).lower().replace('h', ' ').replace('m', ' ').split()
            hours = float(parts[0])
            minutes = float(parts[1]) if len(parts) >= 2 else 0.0
            return hours + (minutes / 60.0)
        except:
            return np.nan

    def ra_to_month(self, ra):
        """Map RA to best viewing month."""
        ra_decimal = self.parse_ra_to_decimal(ra)
        if pd.isna(ra_decimal):
            return "Unknown"

        month_idx = int(ra_decimal / RA_TO_MONTH_BUCKET_SIZE) % MONTHS_IN_YEAR
        return MONTH_MAP.get(month_idx, "Unknown")

    def parse_angular_size(self, size_str):
        """
        Convert angular size string into tuple.

        Examples:
            "6x4" → (6,4)
            "10"  → (10,10)
        """
        if pd.isna(size_str):
            return np.nan
        try:
            parts = str(size_str).lower().replace("'", "").split('x')
            if len(parts) == 2:
                return float(parts[0]), float(parts[1])
            val = float(parts[0])
            return val, val
        except:
            return np.nan

    def normalize_object_type(self, raw_type):
        """Standardize object types for filtering."""
        raw = str(raw_type).lower()
        if "galaxy" in raw:
            return "Galaxy"
        if "nebula" in raw:
            return "Nebula"
        if "cluster" in raw:
            return "Cluster"
        return "Other"

    def classify_size(self, size):
        """Convert numeric size into readable category."""
        if pd.isna(size):
            return "Unknown"
        if size > LARGE_OBJECT_APPARENT_SIZE_LIMIT:
            return "Very Large"
        if size > VERY_LARGE_OBJECT_APPARENT_SIZE_LIMIT:
            return "Large"
        if size > MEDIUM_OBJECT_APPARENT_SIZE_LIMIT:
            return "Medium"
        return "Small"

    def aperture_mag_limit(self, aperture_mm):
        """
        Calculates faintest visible magnitude for a telescope.

         See constants file for source on formula for this!
        """
        if aperture_mm <= 0:
            return 0
        return MAG_BASE_CONSTANT + MAG_LOG_COEFFICIENT * np.log10(aperture_mm)

    def filter_by_aperture_and_brightness(self, aperture_mm=None):
        """
        Filters objects visible with a given telescope aperture.

        NOTE:
        - Aperture affects visibility (brightness)
        - DOES NOT affect apparent size
        """
        target_ap = aperture_mm if aperture_mm else self.default_aperture
        limit = self.aperture_mag_limit(target_ap)

        mag_col = self.columns['MAGNITUDE']

        visible_df = self.df[self.df[mag_col] <= limit].copy()

        visible_df['VisibilityRating'] = visible_df[mag_col].apply(
            lambda m: self._assign_dynamic_rating(m, limit)
        )

        return visible_df.sort_values(by=mag_col)

    def _assign_dynamic_rating(self, mag, mag_limit):
        """Assign observation difficulty."""
        if pd.isna(mag):
            return "Unknown"

        if mag <= NAKED_EYE_BRIGHT_URBAN_VISIBILITY_THRESHOLD:
            return "Naked Eye (Urban)"
        if mag <= NAKED_EYE_SUBURBAN_RURAL_DARK_VISIBILITY_THRESHOLD:
            return "Naked Eye (Dark Sky)"
        if mag <= BINOCULAR_VISIBILITY_THRESHOLD:
            return "Binoculars Recommended"

        if mag > mag_limit:
            return "Not Visible"

        if mag > (mag_limit - 1.0):
            return "Challenging Telescope Target"

        return "Good Telescope Target"

    def get_all_objects(self):
        return self.df.copy()

    def get_objects_by_type(self, object_type):
        return self.df[self.df['NormalizedType'] == object_type].copy()

    def get_object_types(self):
        return self.df[self.columns['TYPE']].unique().tolist()

    def filter_by_magnitude_range(self, min_mag=None, max_mag=None):
        mag_col = self.columns['MAGNITUDE']
        df = self.df.copy()

        if min_mag is not None:
            df = df[df[mag_col] >= min_mag]
        if max_mag is not None:
            df = df[df[mag_col] <= max_mag]

        return df

    def get_visible_in_season(self, season_name):
        try:
            ra_min, ra_max = SEASON_RA[season_name]

            if ra_min > ra_max:
                return self.df[
                    (self.df['RA_Decimal'] >= ra_min) |
                    (self.df['RA_Decimal'] < ra_max)
                ]
            return self.df[
                (self.df['RA_Decimal'] >= ra_min) &
                (self.df['RA_Decimal'] < ra_max)
            ]
        except KeyError:
            logger.warning(f"Invalid season: {season_name}")
            return pd.DataFrame()

    def get_largest_objects(self, top_n=10):
        """Return largest apparent objects."""
        return self.df.sort_values(by='ApparentSizeAvg', ascending=False).head(top_n)

    def explain_aperture_limit(self, aperture_mm=None):
        """
        Prints and returns the magnitude limit for a given aperture.
        Useful for debugging and demonstrations! Fun helpful info for user too.
        """
        aperture = aperture_mm if aperture_mm else self.default_aperture
        limit = self.aperture_mag_limit(aperture)

        logger.info(
            f"APERTURE_ANALYSIS: Aperture={aperture}mm → Limiting Magnitude={limit:.2f}"
        )

        return {
            "aperture_mm": aperture,
            "limiting_magnitude": round(limit, 2)
        }

    def log_filtered_objects(self, df, log_filename):
        with open(log_filename, "w", encoding="utf-8") as f:
            f.write(f"=== Visibility Report | Count: {len(df)} ===\n\n")
            f.write(df.to_string(index=False))

        logger.info(f"LOG_SUCCESS: {log_filename}")
