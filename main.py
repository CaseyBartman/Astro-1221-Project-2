"""
Entry point for the Messier Object Tourist Guide app.
"""


from messier_data_ingester import MessierDataIngester
from constants import CSV_FILENAME, LOG_FILENAME, DEFAULT_APERTURE_MM, DEFAULT_APERTURE_LOG_FILENAME, CUSTOM_APERTURE_LOG_FILENAME
from astro_analytics_engine import AstroAnalyticsEngine
from astro_streamlit_ui import run_streamlit_ui

def main():
    """Main entry point for the app."""
    run_streamlit_ui()

    # OPTIONAL: Print the results from the data parsing for logging. Might be helpful with grading.
    # Just uncomment this next line, comment out the "run_streamlit_ui() line" and run this command: python main.py
    #demonstrate_analytics_results()

def demonstrate_analytics_results(): 
    # 1. Ingest Messier data (console/CLI analytics demo)
    ingester = MessierDataIngester()
    csv_path = ingester.fetch_and_save()
    objects = ingester.parse_messier_objects_to_dict(csv_path)
    ingester.log_objects_to_txt(objects)
    print(f"Downloaded and parsed {len(objects)} Messier objects. Logged to {LOG_FILENAME}.")

    # 2. Initialize analytics engine
    analytics = AstroAnalyticsEngine(objects)
    analytics.clean_data()

    # Test with default aperture
    filtered_df_default = analytics.filter_by_aperture_and_brightness()
    analytics.log_filtered_objects(
        filtered_df_default, 
        log_filename=DEFAULT_APERTURE_LOG_FILENAME
    )
    print(f"Default Aperture ({DEFAULT_APERTURE_MM}mm): {len(filtered_df_default)} objects found.")

    # Test with custom aperture, just check the created file and associated logs
    custom_aperture = 10
    filtered_df_custom = analytics.filter_by_aperture_and_brightness(custom_aperture)
    analytics.log_filtered_objects(
        filtered_df_custom, 
        log_filename=CUSTOM_APERTURE_LOG_FILENAME
    )
    print(f"Custom Aperture ({custom_aperture}mm): {len(filtered_df_custom)} objects found.")



    import logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    logger = logging.getLogger(__name__)
    logger.info("STARTING APPLICATION")

    ingester = MessierDataIngester()
    csv_path = ingester.fetch_and_save()

    objects = ingester.parse_messier_objects_to_dict(csv_path)
    ingester.log_objects_to_txt(objects)

    logger.info(f"INGEST_COMPLETE: {len(objects)} objects loaded")

    analytics = AstroAnalyticsEngine(objects)
    analytics.clean_data()

    logger.info("ANALYTICS_ENGINE_READY") # This is where we start logging the results from the functions in astro_anlytics_engine!

    logger.info("=== APERTURE TESTS ===")
    default_info = analytics.explain_aperture_limit()
    custom_aperture = 10
    custom_info = analytics.explain_aperture_limit(custom_aperture)

    print(f"Default Aperture → Limit: {default_info['limiting_magnitude']}")
    print(f"Custom Aperture ({custom_aperture}mm) → Limit: {custom_info['limiting_magnitude']}")

    logger.info("=== VISIBILITY FILTERING ===")
    filtered_df_default = analytics.filter_by_aperture_and_brightness()
    analytics.log_filtered_objects(
        filtered_df_default,
        log_filename="filtered_objects_default_aperture.txt"
    )

    print(f"Default Aperture: {len(filtered_df_default)} objects visible")
    filtered_df_custom = analytics.filter_by_aperture_and_brightness(custom_aperture)
    analytics.log_filtered_objects(
        filtered_df_custom,
        log_filename="filtered_objects_custom_aperture.txt"
    )

    print(f"Custom Aperture ({custom_aperture}mm): {len(filtered_df_custom)} objects visible")

    logger.info("=== GETTER METHOD DEMOS ===")
    # --- Object Types ---
    types = analytics.get_object_types()
    print("\nAvailable Object Types:")
    print(types)

    # --- Objects by Type ---
    galaxies = analytics.get_objects_by_type("Galaxy")
    print(f"\nGalaxy Count: {len(galaxies)}")

    # --- Magnitude Filtering ---
    bright_objects = analytics.filter_by_magnitude_range(max_mag=6)
    print(f"\nBright Objects (mag ≤ 6): {len(bright_objects)}")

    # --- Seasonal Visibility ---
    spring_objects = analytics.get_visible_in_season("Spring")
    print(f"\nSpring Visible Objects: {len(spring_objects)}")

    # --- Largest Objects ---
    largest_objects = analytics.get_largest_objects(5)
    print("\nTop 5 Largest Objects:")
    print(largest_objects[[analytics.columns['NAME'], 'ApparentSizeAvg']])

    # Combined Example
    logger.info("=== COMBINED QUERY EXAMPLE ===")

    # Example: "What galaxies are visible in spring under mag 8?"
    result = analytics.get_objects_by_type("Galaxy")
    result = result[result[analytics.columns['MAGNITUDE']] <= 8]

    result = result.merge(
        analytics.get_visible_in_season("Spring"),
        how="inner"
    )

    print(f"\nFiltered Spring Galaxies (mag ≤ 8): {len(result)}")

    logger.info("=== REQUIREMENTS DEMONSTRATION ===") #these just show the direct requirements from the project description
    # Requirement: Apparent Size
    print("\n[REQ] Largest Apparent Objects (Size Calculation):")
    largest = analytics.get_largest_objects(5)

    print(
        largest[
            [
                analytics.columns['NAME'],
                'AngularSizeMajor',
                'AngularSizeMinor',
                'ApparentSizeAvg',
                'SizeCategory'
            ]
        ]
    )

    # Requirement: Filter by Season
    print("\n[REQ] Objects Visible in Winter:")
    winter_objects = analytics.get_visible_in_season("Winter")

    print(f"Total Winter Objects: {len(winter_objects)}")
    print(
        winter_objects[
            [
                analytics.columns['NAME'],
                'RA_Decimal',
                'BestViewingMonth'
            ]
        ].head(5)
    )

    # Requirement: Filter by Aperture
    print("\n[REQ] Visibility by Aperture (Default vs 10mm):")

    default_visible = analytics.filter_by_aperture_and_brightness()
    custom_visible = analytics.filter_by_aperture_and_brightness(10)

    print(f"Default Aperture Visible: {len(default_visible)}")
    print(f"10mm Aperture Visible: {len(custom_visible)}")

    # Show faintest object visible in each case
    print("\nFaintest object (Default):")
    print(default_visible.tail(1)[[analytics.columns['NAME'], analytics.columns['MAGNITUDE']]])

    print("\nFaintest object (10mm):")
    print(custom_visible.tail(1)[[analytics.columns['NAME'], analytics.columns['MAGNITUDE']]])

    # Requirement: Filter by Type
    print("\n[REQ] Galaxies Only:")
    galaxies = analytics.get_objects_by_type("Galaxy")
    print(f"Galaxy Count: {len(galaxies)}")

    print(galaxies[[analytics.columns['NAME'], analytics.columns['TYPE']]].head(5))

    # Requirement: Filter by Magnitude Range
    print("\n[REQ] Bright Objects (Magnitude ≤ 6):")
    bright = analytics.filter_by_magnitude_range(max_mag=6)

    print(f"Bright Object Count: {len(bright)}")
    print(bright[[analytics.columns['NAME'], analytics.columns['MAGNITUDE']]].head(5))

    # Requirement: COMBINED REAL QUERY
    print("\n[REQ] Combined Query: Large Galaxies Visible in Summer with Telescope")

    # Step 1: galaxies
    result = analytics.get_objects_by_type("Galaxy")

    # Step 2: visible in summer
    summer = analytics.get_visible_in_season("Summer")
    result = result[result.index.isin(summer.index)]

    # Step 3: visible with telescope
    visible = analytics.filter_by_aperture_and_brightness()
    result = result[result.index.isin(visible.index)]

    # Step 4: large objects only
    result = result[result['SizeCategory'].isin(["Large", "Very Large"])]

    print(f"Matching Objects: {len(result)}")

    print(
        result[
            [
                analytics.columns['NAME'],
                analytics.columns['MAGNITUDE'],
                'ApparentSizeAvg',
                'SizeCategory',
                'BestViewingMonth'
            ]
        ].head(10)
    )

    logger.info("REQUIREMENTS DEMO COMPLETE")

if __name__ == "__main__":
    main()
