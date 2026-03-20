# Astro-1221-Project-2

Architecture:
 - The following classes will all be levereged by the main.py file as our main top-down workflow! The goal of using this lead class was to develop incrementally so each class can work on its own and be tested in isolation! 
Classes:
1) MessierDataIngester class 
- Data Structures: 
  - JSON/CSV byte stream from API
  - List of Dictionaries (list[dict]) where each dict represents one celestial obejct {"name": "...", "type": "Galaxy"... }
- Goal:
  - fetch_and_save() Leverage "requests" library to download the messier catalog to save catalog to local .csv file 
  - parse_messier_objects_to_dict() read CSV and return the list of dictionaries to be used by the analytics engine class

2) AstroAnalyticsEngine class (the pandas implementation class)
- Data Structures: 
  - df (Pandas DataFrame) of the main table containing all 110+ objects
- Goal: 
  - Convert list into a self.df
  - clean_data() Clean the data to make sure data types are appropriate (floats for numbers, not string). Handle NaN's for missing data
  - filter_by_specs(min_mag, obj_type)  returns a subset of the DataFrame to be used to show what specs match the attached spec request
  - calculate_apparent_size(aperture_mm) using pandas vectorized math, adds a new column to the DF calculating how large an object appears based on user gear
  - ger_seaonal_targets(season name): - using filtering, returns objects visible in the current sky

3) UserProfile
- Data Structures: 
  - preferences dict. to store settings for user {"aperture": 114, "location": "Columbus", "level": "Beginner" ...} 
  - Favorites list to contain IDs of objects the user wants to see later
- Goal: 
  - Manage the state of the person using the app
  - update_preferences(key, value) to update the user's dictionary info
  - save_profile()  to export the dictionary to a user_config.json file
  - get_preference(key) safely retrieves a value from the user's preferences


4) AstroLLMTools - converts AI queries into data engine calls
- DataStructures: 
  - list[dict] of specific JSON schemas to tell the LLM info about the functions

- Goal: 
  - get_observing_story(object_name) takes a name, retrieves the row from DataFrame, and sends that data to the LLM to write a "story" about it
  - other function tools for LLM from requirements
  - generate_observing_plan(user_profile) high-level logic that asks the analytics engine for visible tonight objects and formats them into a nice list 

5) AstroStreamlitUI:
- Goal: 
  - render_sidebar() or a similar named function to display UserProfile settings 
  - display_start_chart() - uses matplotlib to plot the objects from the analytics engine
  - chat_interface() - the textbox that talks to the LLM manager to handle user input


## Other Documentation To-Do:
 - Add AI usage to readme 
 - Provide script or command to run or function that shows every markdown comment (//) and prints them using regex into a txt file for grading purposes 
 - Requirements.txt file
 - Dependencies and usagee/installation guide and everything.
