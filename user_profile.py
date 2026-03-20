"""
UserProfile
-----------
Manages user preferences and favorites for the observing companion app.

Classes:
    UserProfile

Methods:
    __init__():
        # Initialize user preferences and favorites
        pass
    update_preferences(key, value):
        # Update a user preference
        pass
    save_profile():
        # Export preferences to user_config.json
        pass
    get_preference(key):
        # Retrieve a preference value safely
        pass

Data Structures:
    - preferences: dict (e.g., {"aperture": 114, "location": "Columbus", ...})
    - favorites: list of Messier object IDs
"""

class UserProfile:
    """Class to manage user preferences and favorites."""
    def __init__(self):
        """Initialize user profile with default preferences and favorites list."""
        pass

    def update_preferences(self, key, value):
        """Update a specific user preference."""
        pass

    def save_profile(self):
        """Export preferences and favorites to a JSON file."""
        pass

    def get_preference(self, key):
        """Safely retrieve a preference value by key."""
        pass
