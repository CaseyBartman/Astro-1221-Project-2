"""
UserProfile
-----------
Manages user preferences and favorites for the observing companion app.
 
Classes:
    UserProfile
 
Methods:
    __init__():
        # Initialize user preferences and favorites
 
    update_preferences(key, value):
        # Update a user preference
 
    save_profile():
        # Export preferences to user_config.json
 
    load_profile():
        # Load preferences from user_config.json if it exists
 
    get_preference(key):
        # Retrieve a preference value safely
 
    add_favorite(messier_id):
        # Add a Messier object ID to favorites
 
    remove_favorite(messier_id):
        # Remove a Messier object ID from favorites
 
    get_favorites():
        # Return the current favorites list
 
    reset_to_defaults():
        # Reset all preferences back to defaults
 
Data Structures:
    - preferences: dict (e.g., {"aperture": 114, "location": "Columbus", ...})
    - favorites: list of Messier object IDs (e.g., ["M1", "M31", "M42"])
"""
 
import json
import os
import logging
from constants import DEFAULT_APERTURE_MM
 
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)
 
# Default file path for saving/loading user profiles
PROFILE_FILENAME = "user_config.json"
 
# Valid experience levels for input validation
VALID_EXPERIENCE_LEVELS = ["Beginner", "Intermediate", "Advanced"]
 
# Valid seasons for input validation
VALID_SEASONS = ["Spring", "Summer", "Fall", "Winter"]
 
# Default preferences for new users
DEFAULT_PREFERENCES = {
    "name": "",
    "location": "Columbus",
    "aperture_mm": DEFAULT_APERTURE_MM,
    "experience_level": "Beginner",
    "preferred_season": "Spring",
}
 
 
class UserProfile:
    """
    Class to manage user preferences and favorites.
 
    Stores observer settings (telescope aperture, location, experience level)
    in a dictionary and maintains a favorites list of Messier object IDs.
    Supports saving/loading to JSON for persistence across sessions.
    """
 
    def __init__(self, profile_path=PROFILE_FILENAME):
        """
        Initialize user profile with default preferences and empty favorites.
 
        If a saved profile exists at profile_path, it will be loaded
        automatically. Otherwise, defaults are used.
 
        Args:
            profile_path (str): Path to the JSON profile file.
        """
        self.profile_path = profile_path
        self.preferences = dict(DEFAULT_PREFERENCES)
        self.favorites = []
 
        # Attempt to load existing profile from disk
        if os.path.exists(self.profile_path):
            self.load_profile()
            logger.info(f"PROFILE_LOADED: {self.profile_path}")
        else:
            logger.info("PROFILE_NEW: Using default preferences")
 
    def update_preferences(self, key, value):
        """
        Update a specific user preference with validation.
 
        Args:
            key (str): The preference key to update.
            value: The new value for the preference.
 
        Returns:
            bool: True if the update was successful, False if validation failed.
        """
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
 
    def get_preference(self, key):
        """
        Safely retrieve a preference value by key.
 
        Args:
            key (str): The preference key to look up.
 
        Returns:
            The preference value, or None if the key doesn't exist.
        """
        value = self.preferences.get(key, None)
        if value is None:
            logger.warning(f"PREFERENCE_NOT_FOUND: '{key}'")
        return value
 
    def add_favorite(self, messier_id):
        """
        Add a Messier object ID to the favorites list.
 
        Args:
            messier_id (str): The Messier ID to add (e.g., "M31").
 
        Returns:
            bool: True if added, False if already in favorites.
        """
        if messier_id in self.favorites:
            logger.info(f"FAVORITE_EXISTS: {messier_id} already in favorites")
            return False
 
        self.favorites.append(messier_id)
        logger.info(f"FAVORITE_ADDED: {messier_id}")
        return True
 
    def remove_favorite(self, messier_id):
        """
        Remove a Messier object ID from the favorites list.
 
        Args:
            messier_id (str): The Messier ID to remove.
 
        Returns:
            bool: True if removed, False if not found.
        """
        if messier_id not in self.favorites:
            logger.warning(f"FAVORITE_NOT_FOUND: {messier_id}")
            return False
 
        self.favorites.remove(messier_id)
        logger.info(f"FAVORITE_REMOVED: {messier_id}")
        return True
 
    def get_favorites(self):
        """
        Return the current favorites list.
 
        Returns:
            list: Copy of the favorites list.
        """
        return list(self.favorites)
 
    def save_profile(self):
        """
        Export preferences and favorites to a JSON file.
 
        Returns:
            bool: True if save was successful, False otherwise.
        """
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
        """
        Load preferences and favorites from a JSON file.
 
        Returns:
            bool: True if load was successful, False otherwise.
        """
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
 
    def reset_to_defaults(self):
        """
        Reset all preferences to defaults and clear favorites.
        """
        self.preferences = dict(DEFAULT_PREFERENCES)
        self.favorites = []
        logger.info("PROFILE_RESET: All preferences restored to defaults")
 
    def __str__(self):
        """Human-readable summary of the user profile."""
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
