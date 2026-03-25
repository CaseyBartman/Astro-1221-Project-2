# ##
# UserProfile
# -----------
# Manages user preferences and favorites for the observing companion app.
# We want to set up a personalized touring experience for the user, so we need to store their preferences and favorites.
# This sets up many of the components of the app, such as the sidebar, the polar sky chart, the scatter finder chart, the object detail cards, the observation log, and the favorites management.
# It's relatively straightforward! This is really just setting up things that the monster of a code the Streamlit is.

# Classes:
#     UserProfile
 
# Methods:
#     __init__(): 
#     update_preferences(key, value): 
#     save_profile(): 
#     load_profile(): 
#     get_preference(key): 
#     add_favorite(messier_id): 
#     remove_favorite(messier_id): 
#     get_favorites(): 
#     reset_to_defaults():
 
# Data Structures:
#     - preferences: dict (e.g., {"aperture": 114, "location": "Columbus", ...})
#     - favorites: list of Messier object IDs (e.g., ["M1", "M31", "M42"])
# ##
 
import json
import os
import logging
from constants import DEFAULT_APERTURE_MM
 
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

#-------------------------------------------------------------------------------------------------------------------------------------------
PROFILE_FILENAME = "user_config.json"

VALID_EXPERIENCE_LEVELS = ["Beginner", "Intermediate", "Advanced"]

VALID_SEASONS = ["Spring", "Summer", "Fall", "Winter"]

DEFAULT_PREFERENCES = {
    "name": "",
    "location": "Columbus",
    "aperture_mm": DEFAULT_APERTURE_MM,
    "experience_level": "Beginner",
    "preferred_season": "Spring",
}
 
 ## these few lines are just constants for the user profile
 ## This tells us what seasons, and experience levels are valid, and the default preferences for a new user.
 ## The valid lists are used later in the code to validate input, so if someone tried to set the experience to expert it would get rejected since it's not on the list
 ## Think of these as a bouncer... maybe thats not a great analogy but i thought it was funny
 # -----------------------------------------------------------------------------------------------------------------------------------

class UserProfile:
## the class manages user preferences and favorites. it stores the observer settings (telescope aperture, location, experience level) 
## in a dictionary and maintains a favorites list of Messier object IDs. it supports saving/loading to JSON for persistence across sessions

#-----------------------------------------------------------------------------------------------------------------------------------
    def __init__(self, profile_path=PROFILE_FILENAME):
  
        ##__init__ actually creates the profile object, and sets up the initial preferences and favorites
        ##So if a profile already exists, it will be loaded automatically, otherwise it will use the default preferences
        ## The favorites start as an empty then it checks if a saved json file exists and if it does then it will load the favorites from that file
        
        self.profile_path = profile_path
        self.preferences = dict(DEFAULT_PREFERENCES)
        self.favorites = []
 
        # Attempt to load existing profile from disk
        if os.path.exists(self.profile_path):
            self.load_profile()
            logger.info(f"PROFILE_LOADED: {self.profile_path}")
        else:
            logger.info("PROFILE_NEW: Using default preferences")
 
 #-----------------------------------------------------------------------------------------------------------------------------------
    def update_preferences(self, key, value):
      
        # Validate experience level if that's what's being updated
        if key == "experience_level" and value not in VALID_EXPERIENCE_LEVELS:
            logger.warning(
                f"INVALID_LEVEL: '{value}' is not valid. "
                f"Choose from {VALID_EXPERIENCE_LEVELS}"
            )
            return False
 
        # Validate preferred season
        if key == "preferred_season" and value not in VALID_SEASONS:
            logger.warning(
                f"INVALID_SEASON: '{value}' is not valid. "
                f"Choose from {VALID_SEASONS}"
            )
            return False
 
        # Validate aperture is a positive number
        if key == "aperture_mm":
            try:
                value = float(value)
                if value <= 0:
                    logger.warning("INVALID_APERTURE: Must be a positive number")
                    return False
            except (ValueError, TypeError):
                logger.warning("INVALID_APERTURE: Must be a numeric value")
                return False
 
        self.preferences[key] = value
        logger.info(f"PREFERENCE_UPDATED: {key} = {value}")
        return True

        ##This takes a key (like aperture_mm) and a value (like 114) and updates the preference dictionary
        ## before it saves we need to make sure it is in a valid list so we validate it for each key being experience, season, and aperture
        ## If it returns false it just fails, and streamlit will call this bit each time you change an input

 #-----------------------------------------------------------------------------------------------------------------------------------
    def get_preference(self, key):

        value = self.preferences.get(key, None)
        if value is None:
            logger.warning(f"PREFERENCE_NOT_FOUND: '{key}'")
        return value

    ## This is function that returns a preference value by key
    ## it uses .get() instead of just [key] so the thing wouldn't crash if the key doesn't exist
    ## if it doesn't exist it returns None, and if it does it will return the value

    #-----------------------------------------------------------------------------------------------------------------------------------
    def add_favorite(self, messier_id):

        if messier_id in self.favorites:
            logger.info(f"FAVORITE_EXISTS: {messier_id} already in favorites")
            return False
 
        self.favorites.append(messier_id)
        logger.info(f"FAVORITE_ADDED: {messier_id}")
        return True
    ##This adds a favorite messier id to the favorites list
    ## it check for duplicates first so it doesn't add the same one twice using the logger.info(favorite_exists)
    ## if it doesn't exist it adds it to the list and returns true

    #-----------------------------------------------------------------------------------------------------------------------------------
    def remove_favorite(self, messier_id):

        if messier_id not in self.favorites:
            logger.warning(f"FAVORITE_NOT_FOUND: {messier_id}")
            return False
 
        self.favorites.remove(messier_id)
        logger.info(f"FAVORITE_REMOVED: {messier_id}")
        return True

        ## remove favorites checks if the object is in the list, if it is it removes it and returns true
        ## if it doesn't exist it returns false

#-----------------------------------------------------------------------------------------------------------------------------------
    def get_favorites(self):

        return list(self.favorites)
 #-----------------------------------------------------------------------------------------------------------------------------------
    def save_profile(self):

        try:
            profile_data = {
                "preferences": self.preferences,
                "favorites": self.favorites,
            }
            with open(self.profile_path, "w", encoding="utf-8") as f:
                json.dump(profile_data, f, indent=2)
            logger.info(f"PROFILE_SAVED: {self.profile_path}")
            return True
        except (IOError, OSError) as e:
            logger.error(f"PROFILE_SAVE_FAILED: {e}")
            return False
        
 
    def load_profile(self):

        try:
            with open(self.profile_path, "r", encoding="utf-8") as f:
                profile_data = json.load(f)
 
            # Merge loaded preferences with defaults so new keys aren't lost
            if "preferences" in profile_data:
                merged = dict(DEFAULT_PREFERENCES)
                merged.update(profile_data["preferences"])
                self.preferences = merged
 
            if "favorites" in profile_data:
                self.favorites = profile_data["favorites"]
 
            return True
        except (IOError, OSError, json.JSONDecodeError) as e:
            logger.error(f"PROFILE_LOAD_FAILED: {e}")
            return False
 
         ##save profile wraps the preferences and favorites in a dictionary and saves it to the json file
         ##load profule reads it back with the json.load() function then merges the loaded preferences with the defaults so new keys aren't lost
         ## this is important because if you wnat to add a new key later, the exsiting profiles won't have it
         ## there are a bunch of try and except bloacks that return true or false so that app doesnt crash in case of file I/O errors

#-------------------------------------------------------------------------------------------------------------------------------------------------
    def reset_to_defaults(self):

        self.preferences = dict(DEFAULT_PREFERENCES)
        self.favorites = []
        logger.info("PROFILE_RESET: All preferences restored to defaults")
    ## this is just creating a fresh start on the prefernces, if want a clean slate it will replace everything with fresh defaults

 #-------------------------------------------------------------------------------------------------------------------------------------------
    def __str__(self):
        
        name = self.preferences.get("name", "Observer")
        if not name:
            name = "Observer"
        level = self.preferences.get("experience_level", "Unknown")
        aperture = self.preferences.get("aperture_mm", "Unknown")
        location = self.preferences.get("location", "Unknown")
        fav_count = len(self.favorites)
        return (
            f"Profile: {name} | {level} | "
            f"{aperture}mm aperture | {location} | "
            f"{fav_count} favorite(s)"
        )
 ## finally! to the end of the code for this section. 
 ## this prints a readable version of the preferences are
 ## all of this is just setting up code to then use in our streamlit code