##
##ASTROSTREAMLITUI
# She's very long. The code looks a lot more menacing than it actually is. It certainly would not have been this long if we had decided to stick to one or two main tabs of the streamlit
# I thought it would have been useful to see the information in different formats, especially if the project is supposed to be a tour guide, it needs to have all of the bells and whistles
# It is broken up by the individual tabs, as you scroll through it you will see code for each tab in streamlit show up in the order it appears in the app
# Depending on the contents ont the tab, the code is anywhere from a couple hundred lines to a few dozen

# What you will see:
#  - data loading 
#  - profile set up
#  - error handling 
#  - sidebar visulization - seen in streamlit
#  - sky chart tab - seen in streamlit
#  - finder chart tab - seen in streamlit
#  - object details - seen in streamlit
#  - catalog explorer - seen in streamlit
#  - observation log - seen in streamlit
#  - classifying favorites 
#  - observation tour - seen in streamlit
#  - observing assiant - seen in streamlit
#  - astrostreamlitui class

## everything with a seen in streamlit next to shows up in our app, anything that does not is background work to help the app run. Most of this code is the bells and whistles of each tab to make it look a little fancy
## there any many methods that were used for this app so I will explain the code tab by tab
## one thing that I thought was super cool was running the code and having the pop up side by side with the terminal for the code
## every time I made a change in the app, you could see the terminal adding new info and updating in real time. It's not super profound but I thought it was neat 


import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import json
import os
from datetime import datetime
 
from messier_data_ingester import MessierDataIngester
from astro_analytics_engine import AstroAnalyticsEngine
from user_profile import UserProfile, VALID_EXPERIENCE_LEVELS, VALID_SEASONS
from constants import DEFAULT_APERTURE_MM, SEASON_RA
from astro_llm_tools import AstroLLMTools
 
## This is the driver behind the streamlit code! All of our other files help support this massive chunk of code
## we will go through the chunks piece by piece explaining why they are there and what they do 

# ──────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────
 
OBSERVATION_LOG_FILE = "observation_log.json"
 
TYPE_COLORS = {
    "Galaxy": "#7F77DD",
    "Nebula": "#1D9E75",
    "Cluster": "#D85A30",
    "Other": "#888780",
}
 
 ## The code creates a JSON file when the user logs their first observation! Its where we save observed objects
 ## And pretty simply, we categorized the different types with a color to see better

# ──────────────────────────────────────────────
# Data Loading (cached so it only runs once)
# ──────────────────────────────────────────────

@st.cache_data
def load_messier_data():

    ingester = MessierDataIngester()
    csv_path = ingester.fetch_and_save()
    objects = ingester.parse_messier_objects_to_dict(csv_path)
    analytics = AstroAnalyticsEngine(objects)
    analytics.clean_data()
    return analytics
 
 ## This function pulls from files messier_data_ingester.py and astro_analytics_engine.py  
 ## This creates an ingester, it downlaods the Messier catalog form the internet and parses it into one list of dictionaries 
 ##It then runs these dictionaries through a Pandas DataFrame and cleans it! Turns certain values into others that the code can better use
 ## the st.cache data functions tells streamlit to only run this code once it wont redownload the catalog everytime
 
def get_user_profile():

    if "profile" not in st.session_state:
        st.session_state.profile = UserProfile()
    return st.session_state.profile
@st.cache_resource
def get_llm_tools():
    return AstroLLMTools()
astro_ai = get_llm_tools()

## The user profile funtion pulls from the userprofile.py, it uses the certain charactersic like name, season preference, etc in the file to complete the profile
## if there is not a profile in the "session" or rather the open tab, it will create a new slate user profile. If one already exists then it will use that one (so if you already run the code and saved your profile it would still be there)
## Everytime anything happens in the streamlit the entire code gets rerun, without this funtion any changes made would lose all of the progress
## using the st.cache resources we can keep the profile from moving when changes are made

##The get llm tools function pulls from the file astro llm tools 
## In that code there is an AstroLLMTools fucntion which we are recalling in this code to create the get observing story and generate observing plan function in streamlit
 
# ──────────────────────────────────────────────
# Observation Log — Persistence
# ──────────────────────────────────────────────
 
def load_observation_log():

    if "obs_log" not in st.session_state:
        if os.path.exists(OBSERVATION_LOG_FILE):
            try:
                with open(OBSERVATION_LOG_FILE, "r", encoding="utf-8") as f:
                    st.session_state.obs_log = json.load(f)
            except (json.JSONDecodeError, IOError):
                st.session_state.obs_log = {}
        else:
            st.session_state.obs_log = {}
    return st.session_state.obs_log
 
 
def save_observation_log():

    try:
        with open(OBSERVATION_LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(st.session_state.obs_log, f, indent=2)
    except IOError as e:
        st.error(f"Could not save observation log: {e}")
 
 ## Our load_obseravtion_log code checks if an observation log already exists, if one doesnt it tries to pull from observation_log.json
 ## And if all else fails it will simply create a new log with an empty dictionary
 ## Again this is just precaution that streamlit doesnt run the code again every time a change is made and lose all of the edits made in the app
 ## st.cache and st.session state are similar commands: st.cache tells stremalit to only run the function once and save that result. st.session state tells it to keep the same variable and not rerun it but the user can change it
 ## in short, cache = run once with no changes, session state = create one, update when needed 

 ## The save_observation_log takes the current observation log from the session writes it to observation_log.json
 ## This command is called every time a user logs, edits, or removes an observation
 ## so like previosly mentioned, st.session_state makes sure its only created once but we change if needed (and this is where that change happens)

# ──────────────────────────────────────────────
# Sidebar — User Profile Settings
# ──────────────────────────────────────────────
 
def render_sidebar(profile, analytics):

    st.sidebar.title("Observer Profile")
 
    # Name
    name = st.sidebar.text_input(
        "Your Name",
        value=profile.get_preference("name") or "",
    )
    if name != profile.get_preference("name"):
        profile.update_preferences("name", name)
 
    # Location
    location = st.sidebar.text_input(
        "Location",
        value=profile.get_preference("location") or "Columbus",
    )
    if location != profile.get_preference("location"):
        profile.update_preferences("location", location)
 
    # Aperture — use a key so Streamlit manages the state directly
    if "aperture_input" not in st.session_state:
        st.session_state.aperture_input = float(
            profile.get_preference("aperture_mm") or DEFAULT_APERTURE_MM
        )
 
    aperture = st.sidebar.number_input(
        "Telescope Aperture (mm)",
        min_value=1.0,
        max_value=1000.0,
        step=1.0,
        key="aperture_input",
    )
    profile.update_preferences("aperture_mm", aperture)
 
    # Experience Level
    current_level = profile.get_preference("experience_level") or "Beginner"
    level_index = VALID_EXPERIENCE_LEVELS.index(current_level)
    level = st.sidebar.selectbox(
        "Experience Level",
        VALID_EXPERIENCE_LEVELS,
        index=level_index,
    )
    if level != profile.get_preference("experience_level"):
        profile.update_preferences("experience_level", level)
 
    # Preferred Season
    current_season = profile.get_preference("preferred_season") or "Spring"
    season_index = VALID_SEASONS.index(current_season)
    season = st.sidebar.selectbox(
        "Preferred Season",
        VALID_SEASONS,
        index=season_index,
    )
    if season != profile.get_preference("preferred_season"):
        profile.update_preferences("preferred_season", season)
 
    # Save button
    if st.sidebar.button("Save Profile"):
        profile.save_profile()
        st.sidebar.success("Profile saved!")
 
    # Stats summary
    st.sidebar.divider()
 
    # Aperture info
    mag_limit = analytics.aperture_mag_limit(aperture)
    st.sidebar.metric("Limiting Magnitude", f"{mag_limit:.1f}")
 
    visible_count = len(analytics.filter_by_aperture_and_brightness(aperture))
    st.sidebar.metric("Visible Objects", f"{visible_count} / 110")
 
    obs_log = load_observation_log()
    st.sidebar.metric("Objects Observed", f"{len(obs_log)} / 110")
 
    st.sidebar.divider()
    st.sidebar.caption(str(profile))
 
    # Reset section
    st.sidebar.divider()
    with st.sidebar.expander("Reset Data"):
        st.caption("Clear all personal data so a new observer can start fresh.")
        if st.button("Reset All Data", type="secondary"):
            st.session_state.confirm_reset = True
 
        if st.session_state.get("confirm_reset", False):
            st.warning("This will erase your profile, favorites, observation log, and all saved data.")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Yes, reset everything", type="primary"):
                    # Reset profile
                    profile.reset_to_defaults()
                    if os.path.exists(profile.profile_path):
                        os.remove(profile.profile_path)
 
                    # Reset observation log
                    if os.path.exists(OBSERVATION_LOG_FILE):
                        os.remove(OBSERVATION_LOG_FILE)
                    st.session_state.obs_log = {}
 
                    # Clear session state
                    for key in list(st.session_state.keys()):
                        del st.session_state[key]
 
                    st.rerun()
            with col2:
                if st.button("Cancel"):
                    st.session_state.confirm_reset = False
                    st.rerun()
 
    return profile
 
 ## This fucntion pulls from quite a few files including user_profile, astro_analytics_engine, and constants
 ## This is all code to edit the actual lay out of streamlit, the st. tells us that this is streamlit
 ## We build the sidebar with inputs for name, location, aperture, experience level, and season
 ## Each input update the profile_prefernces so it stays that way unless the user decided to reset data which is also seen the final block of code
 ## all the other tabs in streamlit rely on the data saved in the profile so it is important the it doesnt change between clicks

# ──────────────────────────────────────────────
# Polar Sky Chart
# ──────────────────────────────────────────────
 
def display_polar_chart(analytics, profile):

    st.subheader("Sky Chart")
    st.caption(
        "A polar view of all Messier objects. Angle = Right Ascension, "
        "distance from center = magnitude (brighter objects are closer to center)."
    )

## this one is a little long so I will be cutting up the commentary, but this first bit of code is not necessary I just thought it would be nice to have a bried description of the tab
## we pull from files astro_analytics_engine (get all objects, get visible in season and filter by aperture and brightness), user_profile (for its get prefernces command), and constants (for the season right acensions) again 
    aperture = profile.get_preference("aperture_mm") or DEFAULT_APERTURE_MM
    season = profile.get_preference("preferred_season") or "Spring"
    mag_col = analytics.columns['MAGNITUDE']
    name_col = analytics.columns['NAME']
    mag_limit = analytics.aperture_mag_limit(aperture)
 
 ## we need to pull all the inputs that the user made in the profile into the sidebar so that we can create a more personalized sky map

    # Filter controls
    col1, col2, col3 = st.columns(3)
    with col1:
        show_season_only = st.checkbox(
            f"Show only {season} objects", value=False, key="polar_season"
        )
    with col2:
        color_mode = st.selectbox(
            "Color by",
            ["Object Type", "Viewing Difficulty"],
            key="polar_color",
        )
    with col3:
        show_visible_only = st.checkbox(
            "Show only visible with my telescope", value=False, key="polar_visible"
        )
## This create the three controls at the top of the sky map, the only real difference in the code here is that we created checked boxes for 1 and 3 and a selecter for 2
       
    df = analytics.get_all_objects().copy()
 
    if show_season_only:
        seasonal = analytics.get_visible_in_season(season)
        df = df[df.index.isin(seasonal.index)]
 
    if show_visible_only:
        visible = analytics.filter_by_aperture_and_brightness(aperture)
        df = df[df.index.isin(visible.index)]
        total_visible = len(visible)
        if total_visible == 110:
            st.info(
                f"All 110 Messier objects are visible with your {aperture:.0f}mm "
                f"telescope (limiting mag {mag_limit:.1f}). Try a smaller aperture "
                f"in the sidebar to see the filter in action."
            )
 
    plot_df = df.dropna(subset=['RA_Decimal', mag_col]).copy()
 
    if plot_df.empty:
        st.warning("No objects match the current filters.")
        return

## if the controls we created eailer are clicked or change, this code will display what the controls are doing
## so if show season only is clicked than the sky map will display only the part of sky you can see during that season
 
    # Convert RA hours (0-24) to radians (0 to 2*pi)
    theta = plot_df['RA_Decimal'].values * (2 * np.pi / 24)
 
    # Magnitude as radius (brighter = smaller number = closer to center)
    r = plot_df[mag_col].values
 
    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw={'projection': 'polar'})
    fig.patch.set_alpha(0.0)
    ax.set_facecolor("#0a0a2e")
 
    # Season shading
    ra_min, ra_max = SEASON_RA.get(season, (0, 24))
    theta_min = ra_min * (2 * np.pi / 24)
    theta_max = ra_max * (2 * np.pi / 24)
    if ra_min < ra_max:
        ax.fill_between(
            np.linspace(theta_min, theta_max, 50),
            0, 12, alpha=0.1, color="#1D9E75",
        )
    else:
        ax.fill_between(
            np.linspace(theta_min, 2 * np.pi, 50),
            0, 12, alpha=0.1, color="#1D9E75",
        )
        ax.fill_between(
            np.linspace(0, theta_max, 50),
            0, 12, alpha=0.1, color="#1D9E75",
        )
 
    # Magnitude limit circle
    limit_theta = np.linspace(0, 2 * np.pi, 100)
    ax.plot(limit_theta, [mag_limit] * 100, color="#D85A30",
            linestyle="--", alpha=0.5, linewidth=1, label=f"Scope limit ({mag_limit:.1f})")
 
    # Difficulty color map
    DIFFICULTY_COLORS = {
        "Naked Eye": "#FCDE5A",
        "Binoculars": "#5DCAA5",
        "Telescope": "#7F77DD",
        "Challenging": "#D85A30",
    }

## In short, we created a circular Matplotlib plot using polar projection, each object is a dot where the angle around the circle is the object's Right Ascension and the distance from the center is the mag
 
    def get_difficulty(mag_val):
        if mag_val <= 5.0:
            return "Naked Eye"
        elif mag_val <= 8.5:
            return "Binoculars"
        elif mag_val <= mag_limit - 1.0:
            return "Telescope"
        else:
            return "Challenging"
 
    if color_mode == "Viewing Difficulty":
        plot_df['Difficulty'] = plot_df[mag_col].apply(get_difficulty)
        for diff, color in DIFFICULTY_COLORS.items():
            mask = plot_df['Difficulty'] == diff
            if not mask.any():
                continue
            sizes = plot_df.loc[mask, 'ApparentSizeAvg'].fillna(3).clip(lower=1)
            sizes = (sizes / sizes.max()) * 150 + 25
            ax.scatter(
                theta[mask.values], r[mask.values],
                c=color, s=sizes, alpha=0.85,
                label=f"{diff} ({mask.sum()})",
                edgecolors="white", linewidths=0.5, zorder=5,
            )

## Inside of the display_polar_chart function we have a function that runs if the users chooses to view the skymap by the object's difficulty to see
## It takes magnitudes and sets intervals for them and assigns the intervals to a certain difficulty 

    else:
        # Plot objects by type (original mode)
        for obj_type, color in TYPE_COLORS.items():
            mask = plot_df['NormalizedType'] == obj_type
            if not mask.any():
                continue
            sizes = plot_df.loc[mask, 'ApparentSizeAvg'].fillna(3).clip(lower=1)
            sizes = (sizes / sizes.max()) * 150 + 25
            ax.scatter(
                theta[mask.values], r[mask.values],
                c=color, s=sizes, alpha=0.85,
                label=f"{obj_type} ({mask.sum()})",
                edgecolors="white", linewidths=0.5, zorder=5,
            )
 
        ax.scatter(
            theta[mask.values],
            r[mask.values],
            c=color,
            s=sizes,
            alpha=0.85,
            label=f"{obj_type} ({mask.sum()})",
            edgecolors="white",
            linewidths=0.5,
            zorder=5,
        )
 
    # Label bright/notable objects
    bright_mask = plot_df[mag_col] <= 5.5
    for _, row in plot_df[bright_mask].iterrows():
        t = row['RA_Decimal'] * (2 * np.pi / 24)
        ax.annotate(
            row[name_col],
            xy=(t, row[mag_col]),
            xytext=(5, 5),
            textcoords="offset points",
            fontsize=7,
            color="white",
            alpha=0.8,
        )
   

    # Configure polar axes
    ax.set_theta_zero_location("N")
    ax.set_theta_direction(-1)
 
    # RA hour labels
    hour_labels = [f"{h}h" for h in range(0, 24, 2)]
    ax.set_xticks(np.linspace(0, 2 * np.pi, 12, endpoint=False))
    ax.set_xticklabels(hour_labels, fontsize=9, color="lightgray")
 
    ax.set_ylim(0, 12)
    ax.set_yticks([2, 4, 6, 8, 10])
    ax.set_yticklabels(
        ["mag 2", "mag 4", "mag 6", "mag 8", "mag 10"],
        fontsize=8, color="gray",
    )
 
    ax.grid(True, alpha=0.2, color="gray")
    ax.legend(
        loc="upper right",
        bbox_to_anchor=(1.3, 1.1),
        fontsize=9,
        facecolor="#1a1a3e",
        edgecolor="gray",
        labelcolor="white",
    )
 
    st.pyplot(fig)
    plt.close(fig)
 
    # Info metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Objects Shown", len(plot_df))
    col2.metric("Telescope Limit", f"mag {mag_limit:.1f}")
    col3.metric(f"{season} Season", f"{len(analytics.get_visible_in_season(season))} objects")
 
## Finally, this is just plotting a graph with all of the information we already told streamlit to take into account 

# # ──────────────────────────────────────────────
# Scatter Finder Chart
# ──────────────────────────────────────────────
 
def display_scatter_chart(analytics, profile):
 
## similar to our previous tab, the scatter finder chart pulls all of the same files since it is essentially the same data just organized in a different manner
## Instead of a polar sky chart, this is the traditional rectangular plot that shows the Magnitude vs The RA
## the lower values on the vertical axis show the brighter stars, and going along the horizontal axis shows the body's eastward angular distance
## 1 hour is the same as 15 degrees of angular distances

    st.subheader("Finder Chart (RA vs Magnitude)")
 
    aperture = profile.get_preference("aperture_mm") or DEFAULT_APERTURE_MM
    season = profile.get_preference("preferred_season") or "Spring"
    mag_col = analytics.columns['MAGNITUDE']
    name_col = analytics.columns['NAME']
    mag_limit = analytics.aperture_mag_limit(aperture)
 
    col1, col2 = st.columns(2)
    with col1:
        show_season = st.checkbox(
            f"Show only {season} objects", value=False, key="scatter_season"
        )
    with col2:
        show_visible = st.checkbox(
            "Show only visible with my telescope", value=False, key="scatter_visible"
        )
 
    df = analytics.get_all_objects().copy()
 
    if show_season:
        seasonal = analytics.get_visible_in_season(season)
        df = df[df.index.isin(seasonal.index)]
 
    if show_visible:
        visible = analytics.filter_by_aperture_and_brightness(aperture)
        df = df[df.index.isin(visible.index)]
        if len(visible) == 110:
            st.info(
                f"All 110 Messier objects are visible with your {aperture:.0f}mm "
                f"telescope. Try a smaller aperture to see the filter in action."
            )
 
    plot_df = df.dropna(subset=['RA_Decimal', mag_col]).copy()
 
    if plot_df.empty:
        st.warning("No objects match the current filters.")
        return
 
## It reads the user's aperture and season from the profile then it grabs all 110 objects. The checked boxes that were avalible in our previous tab are also here in this tab
## you can filter the objects by season or by telescope visibilty. If your telescope has a large aperture then it is likely you will be able to see everything 
## and the app tells you that there is nothing you cannot see and to maybe try a smaller aperture to see what the filter does

    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_alpha(0.0)
    ax.set_facecolor("none")
 
    for obj_type, color in TYPE_COLORS.items():
        subset = plot_df[plot_df['NormalizedType'] == obj_type]
        if subset.empty:
            continue
 
        sizes = subset['ApparentSizeAvg'].fillna(3).clip(lower=1)
        sizes = (sizes / sizes.max()) * 150 + 20
 
        ax.scatter(
            subset['RA_Decimal'],
            subset[mag_col],
            c=color,
            s=sizes,
            alpha=0.7,
            label=f"{obj_type} ({len(subset)})",
            edgecolors="white",
            linewidths=0.5,
        )
 
    ax.invert_yaxis()
    ax.set_xlabel("Right Ascension (hours)", fontsize=12)
    ax.set_ylabel("Magnitude (brighter up)", fontsize=12)
    ax.set_xlim(0, 24)
    ax.legend(loc="upper right", fontsize=9)
    ax.grid(True, alpha=0.3)
    ax.tick_params(colors="gray")
    ax.xaxis.label.set_color("gray")
    ax.yaxis.label.set_color("gray")
 
    # Season shading
    ra_min, ra_max = SEASON_RA.get(season, (0, 24))
    if ra_min < ra_max:
        ax.axvspan(ra_min, ra_max, alpha=0.08, color="#1D9E75")
    else:
        ax.axvspan(ra_min, 24, alpha=0.08, color="#1D9E75")
        ax.axvspan(0, ra_max, alpha=0.08, color="#1D9E75")
 
    # Magnitude limit line
    ax.axhline(y=mag_limit, color="#D85A30", linestyle="--", alpha=0.5, linewidth=1)
    ax.text(0.5, mag_limit + 0.2, f"Telescope limit (mag {mag_limit:.1f})",
            fontsize=8, color="#D85A30", alpha=0.7)
 
    st.pyplot(fig)
    plt.close(fig)
 
    st.caption(
        f"Showing {len(plot_df)} objects. Dot size = apparent angular size. "
        f"Green shading = {season} RA range. "
        f"Dashed line = faintest visible with {aperture:.0f}mm aperture."
    )
 
## then it creates a flat scatter plot using matplotlib. The x axis was defines as RA from 0 to 24hr and the Y axis is magnitude
## each dot is again colored by their type using the same dictionary as the polar chart, the dot size relfects the object's apparent size (how big we view the object to be)
## with the season shading section, depending on the user's preferred season, streamlit will highlight the part of the plot where object are seen during that seaosn
## what we will see is that for some seasons, the shaded region is smaller or bigger. For example, summer has a larger shaded region since the Earth moves slower in its...
## orbit around the Sun in its aphelion. And in winter, Earth moves much quicker when it's in perihelion. This is why the objects seem to move faster through the winter months
 
# ──────────────────────────────────────────────
# Object Detail Cards
# ──────────────────────────────────────────────
 
def display_object_details(analytics, profile):

    st.subheader("Object Details")
 
    name_col = analytics.columns['NAME']
    mag_col = analytics.columns['MAGNITUDE']
    type_col = analytics.columns['TYPE']
    ra_col = analytics.columns['RA']
    dec_col = analytics.columns['DEC']
    constellation_col = analytics.columns['CONSTELLATION']
    size_col = analytics.columns['ANGULAR_SIZE']
    remarks_col = analytics.columns['REMARKS']
 
    aperture = profile.get_preference("aperture_mm") or DEFAULT_APERTURE_MM
 
    # Object selector
    all_names = sorted(analytics.df[name_col].dropna().unique().tolist())
    selected = st.selectbox("Select a Messier Object", all_names, key="detail_select")
 
    if not selected:
        return
 
    row = analytics.df[analytics.df[name_col] == selected].iloc[0]
    obs_log = load_observation_log()
    is_observed = selected in obs_log
 
    # Header with observation status
    header_col1, header_col2 = st.columns([3, 1])
    with header_col1:
        st.markdown(f"### {selected}")
        st.caption(f"{row.get('NormalizedType', 'Unknown')} in {row.get(constellation_col, 'Unknown')}")
    with header_col2:
        if is_observed:
            st.success("Observed!")
        else:
            st.info("Not yet observed")

## This chunk builds a dropdown for all 110 objects, when one is picked it grabs the object's entire row from the analytics engine's DataFrame
## The observation log is checked to see if the object has been observed. Then it shows a header with the name, type, and it tells you it was observed or not yet observed


    # Stats grid
    col1, col2, col3, col4 = st.columns(4)
 
    with col1:
        mag_val = row.get(mag_col, "N/A")
        if mag_val != "N/A":
            st.metric("Magnitude", f"{mag_val:.1f}")
        else:
            st.metric("Magnitude", "N/A")
 
    with col2:
        st.metric("Best Month", row.get('BestViewingMonth', 'Unknown'))
 
    with col3:
        size_avg = row.get('ApparentSizeAvg', None)
        if size_avg and not np.isnan(size_avg):
            st.metric("Apparent Size", f"{size_avg:.1f}'")
        else:
            st.metric("Apparent Size", "N/A")
 
    with col4:
        st.metric("Size Category", row.get('SizeCategory', 'Unknown'))
 
## The four metrics are shown side by side (magnitude, best viewing month, apparent size, and size category)
## each one of these metrics use st.metric to display a label since these 4 facts are likely the most practical numbers for someone hoping to catch a glimpse at one of these objects

    # Position and classification
    col1, col2, col3 = st.columns(3)
 
    with col1:
        st.markdown("**Position**")
        st.text(f"RA:  {row.get(ra_col, 'N/A')}")
        st.text(f"Dec: {row.get(dec_col, 'N/A')}")
 
    with col2:
        st.markdown("**Classification**")
        st.text(f"Type: {row.get(type_col, 'N/A')}")
        ngc_col = analytics.columns.get('NGC', None)
        if ngc_col and ngc_col in analytics.df.columns:
            st.text(f"NGC:  {row.get(ngc_col, 'N/A')}")
 
    with col3:
        # Visibility assessment
        st.markdown("**Visibility**")
        mag_limit = analytics.aperture_mag_limit(aperture)
        mag_val = row.get(mag_col, None)
        if mag_val and not np.isnan(mag_val):
            if mag_val <= 3.0:
                st.text("Naked eye (urban)")
            elif mag_val <= 5.0:
                st.text("Naked eye (dark sky)")
            elif mag_val <= 8.5:
                st.text("Binoculars recommended")
            elif mag_val <= mag_limit:
                st.text("Telescope target")
            else:
                st.text(f"Needs >{aperture:.0f}mm aperture")
        else:
            st.text("Unknown")

## The first column shows RA and Declination, giving the user the sky coordinates needed to figure out where the object is in the sky
## The second column shows the detailed object class, so it is a galaxy, it will specify if it is a Spiral Galaxy
## Finally, the last column shows a visibility assessment, depending on the magnitude the code will run if elif statements to figure out which category the magnitude belongs in
 
    # Remarks
    remarks = row.get(remarks_col, "")
    if remarks and str(remarks).strip() and str(remarks) != "nan":
        st.markdown("**Notes**")
        st.info(str(remarks))
    # Ai story 
    st.divider()
    if st.button(f"Generate AI Cosmic Story for {selected}"):
        with st.spinner(f"Consulting the archives for {selected}..."):
            # We convert the row to a dict to give the AI all the stats
            story = astro_ai.get_observing_story(row.to_dict())
            st.markdown("### 📖 Discovery Lore & Facts")
            st.write(story)

## The AI story create a small clickable at the bottom on the page in order to generate a story about the object

    # Quick actions
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        favorites = profile.get_favorites()
        if selected in favorites:
            if st.button("Remove from Favorites", key="detail_unfav"):
                profile.remove_favorite(selected)
                profile.save_profile()
                st.rerun()
        else:
            if st.button("Add to Favorites", key="detail_fav"):
                profile.add_favorite(selected)
                profile.save_profile()
                st.rerun()
    with col2:
        if not is_observed:
            if st.button("Mark as Observed", key="detail_observe"):
                obs_log[selected] = {
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "notes": "",
                }
                save_observation_log()
                st.rerun()
 
## Finally, we created two buttons at the side of whatever object the user picks, one can either add the oject to their favorites or remove the object from their favorites
## and the other can mark that the object has been observed, allowing the user to keep track of the objects they've seen or haven't yet seen

# ──────────────────────────────────────────────
# Data Table with Filters
# ──────────────────────────────────────────────
 
def display_object_table(analytics, profile):

    st.subheader("Catalog Browser")
 
    aperture = profile.get_preference("aperture_mm") or DEFAULT_APERTURE_MM
    mag_col = analytics.columns['MAGNITUDE']
    name_col = analytics.columns['NAME']
    type_col = analytics.columns['TYPE']
 
## The user's aperture is loaded in from the prfile. The three _col are shortcuts to the actual column names in the CSV, it's just a little easier than typing 'Magnitude' for example!
## We pull those anayltics from the constants file through the analytics engine. thank you casey
## This is very similar to what we have been doing for each tab, just tweaked depending on what we need to import for this bit

    # Filter controls
    col1, col2, col3 = st.columns(3)
 
    with col1:
        types = ["All"] + sorted(
            analytics.df['NormalizedType'].dropna().unique().tolist()
        )
        selected_type = st.selectbox("Object Type", types)
 
    with col2:
        max_mag = st.slider(
            "Max Magnitude (fainter limit)",
            min_value=1.0,
            max_value=13.0,
            value=13.0,
            step=0.5,
        )
 
    with col3:
        selected_season = st.selectbox(
            "Season Filter",
            ["All"] + VALID_SEASONS,
        )
 
## We created three side by side columns. The first col1 is a drop down of the object types
## it reads from the NormalizedType column and sorts it alphabetically. So what we should see in streamlit is a dropdown of options of 'all, cluster, galaxy, nebula, other' 
## The second column col2 creates a magnitude slider between 1 and 13, since the brightness and faintest appearant magnitudes are no greater than about 12.2 and less than 1
## Finally, col3 similar to col2 will create another dropdown, pulling from the valid seasons. This will look like 'all, spring, summer, fall, winter' and you can choose whichever you wish!

    df = analytics.get_all_objects().copy()
 
    if selected_type != "All":
        df = df[df['NormalizedType'] == selected_type]
 
    df = df[df[mag_col] <= max_mag]
 
    if selected_season != "All":
        seasonal = analytics.get_visible_in_season(selected_season)
        df = df[df.index.isin(seasonal.index)]

## The copy at the beginning is just so that the original DataFrame stays unchanged when filters are run over the different types
## The filters run one at a time, if a type is a selected (if we chose galaxies) then it only keep the rpw in NormalizedType that matches galaxies
## After that filter, it will run with the next column, checking what the max magnitude was in the slider. Depending on that slider, it will remove any of the data from the chart that is fainter
## And if a season if selected it will check which season was clicked then check the objects from the analytics engine and keep only the objects that match the selected season
   
    mag_limit = analytics.aperture_mag_limit(aperture)
    df['Visible'] = df[mag_col].apply(
        lambda m: "Yes" if m <= mag_limit else "No"
    )

    obs_log = load_observation_log()
    df['Observed'] = df[name_col].apply(
        lambda n: "Yes" if n in obs_log else ""
    )
## mag_limit calculates the faintest magnitude that the user's aperture would be able to observe 
## Depending on that magnitude limit, if the magnitide is within that limit it writes 'yes' and if not it will write 'no'
## this is the exact same pattern for the observed section, it's checking if the object's names exist in the observaion log dict 

    display_cols = [
        name_col, type_col, mag_col,
        'NormalizedType', 'BestViewingMonth',
        'ApparentSizeAvg', 'SizeCategory', 'Visible', 'Observed',
    ]
    display_cols = [c for c in display_cols if c in df.columns]
 
    st.dataframe(
        df[display_cols].reset_index(drop=True),
        use_container_width=True,
        height=400,
    )
 
    st.caption(
        f"Showing {len(df)} objects. "
        f"Visibility based on {aperture:.0f}mm aperture "
        f"(limiting mag {mag_limit:.1f})."
    )
 
## This is the final thing that builds off the code we wrote before in this section. It will display the name, the type of object, magnitude, and then all of the strings listed after
## It will look like a large data table with the display as the upper row with the each objects details in the correct columns
## the second display_cols is a check which filters out any column name that doesn't exist in the DataFrame, just in case, if someone were to rename a column in the data the code pulls from
## st.dataframe renders the interactive table and reset index simply means to start the row numbers at 0 instead of assigning the rows to be what they were in the DataFrame index

# ──────────────────────────────────────────────
# Observation Log
# ──────────────────────────────────────────────
 
def display_observation_log(analytics, profile):

    st.subheader("Observation Log")
 
    name_col = analytics.columns['NAME']
    mag_col = analytics.columns['MAGNITUDE']
    type_col = analytics.columns['TYPE']
 
    obs_log = load_observation_log()
 
    # Progress bar
    progress = len(obs_log) / 110
    st.progress(progress, text=f"{len(obs_log)} of 110 Messier objects observed ({progress:.0%})")
 
## I think that this is just a cute little detail, it takes the number of logged objects out of the total objects as a decimal which then becomes a percentage in the progress bar
## I have always liked seeing my progress in a more physical form rather than just a number out of the total. Honestly, this and many of the small additions are me just wanting it to look more aesthetic and maybe others will enjoy it too

    # Add new observation
    st.markdown("#### Log a New Observation")
 
    observed_names = list(obs_log.keys())
    unobserved = sorted([
        n for n in analytics.df[name_col].dropna().unique()
        if n not in observed_names
    ])

## We only want to show the unobserved objects in the drop down since its an observation log. It would be rather silly to want to log a new observation and need to scroll through stuff you've already seen
## This gets the list stored of already observed objects and builds a list of anything that is not observed, we will use that list in our dropdown on the tab
 
    if unobserved:
        col1, col2 = st.columns(2)
        with col1:
            new_obj = st.selectbox(
                "Select object",
                ["(Select)"] + unobserved,
                key="log_select",
            )
        with col2:
            obs_date = st.date_input("Date observed", value=datetime.now())
 
        obs_notes = st.text_area(
            "Observation notes (conditions, what you saw, equipment used)",
            placeholder="e.g., Clear skies, saw spiral arms with averted vision...",
            key="log_notes",
        )
 
        if st.button("Log Observation") and new_obj != "(Select)":
            obs_log[new_obj] = {
                "date": obs_date.strftime("%Y-%m-%d"),
                "notes": obs_notes,
            }
            save_observation_log()
            st.success(f"Logged {new_obj}!")
            st.rerun()
    else:
        st.success("You've observed all 110 Messier objects! Congratulations!")

## so if there are any unobserved objects left (if you have already logged all objects there will be the little saying at the end instead of the drop down) you will have a dropdown of unobserved objects and a calendar to choose the date of observation
##col1 covers the object dropdown and col2 covers the date picker
## There's also a little section under the two dropdowns for any notes at all, we put the examples for notes to be describing what the user sees but it could be the weather or even how it made you feel to see the object
## And finally, if we get through all of that, there is a button to log your observation, which saves the date and your notes as well 
 
    # Display log
    if obs_log:
        st.markdown("#### Your Observations")

        sorted_log = sorted(
            obs_log.items(),
            key=lambda x: x[1].get("date", ""),
            reverse=True,
        )

## If there are any observations already logged, you can see them under a section called 'Your Observations' with a dropdown of the object, date, and your notes
## I feel like it's easier to have that there since we previously only told streamlit to display the objects NOT observed in the dropdown. So if you didnt know where to find your logged ones, its in there!
 
        for obj_name, entry in sorted_log:
            obj_row = analytics.df[analytics.df[name_col] == obj_name]
 
            if not obj_row.empty:
                obj_row = obj_row.iloc[0]
                obj_type = obj_row.get('NormalizedType', 'Unknown')
                obj_mag = obj_row.get(mag_col, 'N/A')
 
                with st.expander(
                    f"{obj_name} — {obj_type} | "
                    f"mag {obj_mag} | "
                    f"Observed: {entry.get('date', 'Unknown')}"
                ):
                    if entry.get("notes"):
                        st.write(entry["notes"])
                    else:
                        st.caption("No notes recorded.")
 
                    col1, col2 = st.columns(2)
                    with col1:
                        updated_notes = st.text_area(
                            "Update notes",
                            value=entry.get("notes", ""),
                            key=f"edit_{obj_name}",
                        )
                        if st.button("Save Notes", key=f"save_{obj_name}"):
                            obs_log[obj_name]["notes"] = updated_notes
                            save_observation_log()
                            st.success("Notes updated!")
                            st.rerun()
 
                    with col2:
                        if st.button(
                            "Remove from Log",
                            key=f"remove_{obj_name}",
                        ):
                            del obs_log[obj_name]
                            save_observation_log()
                            st.rerun()
## This beefy thing of a loop loops through each observation. For each one, it looks up the object in the enelytics engine to get its type and mag
## this loop builds off of the concept of the last block, expect now we're actually coding it here. This is the code behind making "Your Observations" work!
## It creates a expander with the object name, type, mag, and date as the header and inside the expander you can see the notes you recorded. Or if there were no notes, then "no notes recorded"
## I wanted to be able and go back to edit any notes if I so chose, so the lower part lets you edit the notes with a save button
## And if you ever wanted to you could delete the entry, whether the user wanted to completely redo their observation and they don't like the object any more

    else:
        st.info(
            "No observations logged yet. Select an object above "
            "to start tracking your Messier marathon!"
        )
 
 
# ──────────────────────────────────────────────
# Favorites
# ──────────────────────────────────────────────
 
## there is an option in a couple of the tabs to add an object to your favorites. It creates a more personalized feel, and if you really really wanted to keep track of a couple object that you liked, then this is the app for you
## I bet we could sell this idea
## the favorites can be viewed under the Object Details Tab to the right, but you can add an object to your favorites through that same tab or through the observing tour

def display_favorites(analytics, profile):

    st.subheader("Favorites")
 
    name_col = analytics.columns['NAME']
    mag_col = analytics.columns['MAGNITUDE']
    type_col = analytics.columns['TYPE']
 
    favorites = profile.get_favorites()
 
    available_names = sorted(analytics.df[name_col].dropna().unique().tolist())
 
    col1, col2 = st.columns(2)
 
    with col1:
        add_fav = st.selectbox(
            "Add to favorites",
            ["(Select)"] + [n for n in available_names if n not in favorites],
            key="add_fav",
        )
        if add_fav != "(Select)":
            if st.button("Add"):
                profile.add_favorite(add_fav)
                profile.save_profile()
                st.rerun()
 
    with col2:
        if favorites:
            remove_fav = st.selectbox(
                "Remove from favorites",
                ["(Select)"] + favorites,
                key="remove_fav",
            )
            if remove_fav != "(Select)":
                if st.button("Remove"):
                    profile.remove_favorite(remove_fav)
                    profile.save_profile()
                    st.rerun()
        else:
            st.info("No favorites yet!")
## col1 creates an add to favorites section and col2 creates a remove from favorites
## under the object details tab you will see the favorites section, the left column has an "add" dropdown that only show objects that are not in the favories this is done by the [n for n in...]
## when you click add it will save it to json and then rerun
## col2 or the right column only appears if you already have favorites to remove. It shows a dropdown of the current favorites. If you click one, you can click a "remove" button to remove it
## it runs the same as col1 in the way that it works 

    if favorites:
        fav_df = analytics.df[analytics.df[name_col].isin(favorites)]
        fav_display = [
            c for c in [
                name_col, type_col, mag_col,
                'BestViewingMonth', 'SizeCategory', 'NormalizedType',
            ]
            if c in fav_df.columns
        ]
        st.dataframe(
            fav_df[fav_display].reset_index(drop=True),
            use_container_width=True,
        )
 
## This is the magic of the favorites section happens
## It first filters the 110 objects to rows of only objects that are in the favorites list
## It renders the favorites table using the list of favorites previously checked 
 
# ──────────────────────────────────────────────
# Observing Tour — Equipment-Based Custom Tours
# ──────────────────────────────────────────────
 
def generate_observing_tip(row, mag_col, aperture, mag_limit):

    mag = row.get(mag_col, None)
    obj_type = row.get('NormalizedType', 'Unknown')
    size_cat = row.get('SizeCategory', 'Unknown')
    name = row.get('Name', 'This object')
 
    tips = []

## Our observing tour gives the user a few different objects to find in the sky and then mark down in the app
## it would be rather cruel to give them a name and then nothing else, so there are a couple tips for them based on different conditions
## tips creates a blank list that will be added to depending on the values of the object 
 
    # Brightness-based tip
    if mag and mag <= 3.0:
        tips.append("Visible to the naked eye even in cities.")
    elif mag and mag <= 5.0:
        tips.append("Naked eye target under dark skies.")
    elif mag and mag <= 8.5:
        tips.append("Best with binoculars or a small scope.")
    elif mag and mag <= mag_limit:
        tips.append(f"Requires your telescope ({aperture:.0f}mm).")

## first tip is dependent on the brightness of the object! 
## this runs through a couple if statements to determine where the object's mag is
## for example, if the object had a magnitude of about 5, the first statement is not true, 5 is not less than or equal to 3, so it goes to the next, and yes! 5 is less than or equal to 5
## so streamlit will print a small hint about viewing the object
 
    # Size-based tip
    if size_cat == "Very Large":
        tips.append("Very large — use low magnification for the best view.")
    elif size_cat == "Large":
        tips.append("Large target — fits well in a wide-field eyepiece.")
    elif size_cat == "Small":
        tips.append("Compact — try higher magnification to see detail.")

## second tip is size dependent, just like the last block, expect this time we don't need if statements because there is not a range for size. At least not for us
## we have only categorized very large, large and small. Depending  on the object was charcertized in the analytics engine it will print a hint

    # Type-based tip
    if obj_type == "Galaxy":
        tips.append("Look for a faint fuzzy glow. Averted vision helps.")
    elif obj_type == "Nebula":
        tips.append("A nebula filter can improve contrast significantly.")
    elif obj_type == "Cluster":
        tips.append("Star cluster — should resolve into individual stars.")
 
    return " ".join(tips) if tips else "Point your telescope and enjoy the view!"
 
## final tip is object dependent, this runs exactly like the size tip. Both are not ranges and only needs to check the data used previously
## the last line puts all of the individual tips into one line, easier viewing
 
def display_observing_tour(analytics, profile):

    st.subheader("Your Observing Tour")
 
    aperture = profile.get_preference("aperture_mm") or DEFAULT_APERTURE_MM
    season = profile.get_preference("preferred_season") or "Spring"
    level = profile.get_preference("experience_level") or "Beginner"
    location = profile.get_preference("location") or "Unknown"
    mag_col = analytics.columns['MAGNITUDE']
    name_col = analytics.columns['NAME']
    type_col = analytics.columns['TYPE']
 
    mag_limit = analytics.aperture_mag_limit(aperture)
    obs_log = load_observation_log()
 
    st.markdown(
        f"A custom tour for a **{level}** observer in **{location}** "
        f"using a **{aperture:.0f}mm** telescope during **{season}**."
    )
 
    # Configure tour size and difficulty by experience level
    if level == "Beginner":
        tour_size = 8
        # Beginners: brightest objects, skip anything near the limit
        mag_ceiling = min(mag_limit, 8.5)
        include_challenge = True
        challenge_ceiling = min(mag_limit, 10.0)
    elif level == "Intermediate":
        tour_size = 12
        mag_ceiling = min(mag_limit, 10.0)
        include_challenge = True
        challenge_ceiling = mag_limit
    else:  # Advanced
        tour_size = 16
        mag_ceiling = mag_limit
        include_challenge = True
        challenge_ceiling = mag_limit

## Based on the experience set in the profile, there are 3 tours avaliable to you
## it goes from beginner, to intermediate, and if it's anything else its immediately advanced 
## the tour size sets how many objects to include, mag ceiling is the faintest main target allowed, the lower level you are the lower mag your main target is
 
    # Get seasonal objects visible with this telescope
    seasonal_df = analytics.get_visible_in_season(season)
    visible_df = analytics.filter_by_aperture_and_brightness(aperture)
 
    # Intersection: seasonal AND visible
    tour_df = seasonal_df[seasonal_df.index.isin(visible_df.index)].copy()
 
    if tour_df.empty:
        st.warning(
            f"No objects found for {season} with a {aperture:.0f}mm telescope. "
            "Try changing your season or aperture in the sidebar."
        )
        return
 
## This gets two dataframes, all objects visible in the selected season and all objects visible with user's telescope
## the long line of tour_df makes sure to keep objects that belong to BOTH of these dataframes, if nothing is able to pass those filters for some reason it will print a warning

    # Split into difficulty tiers
    easy = tour_df[tour_df[mag_col] <= 5.0].sort_values(mag_col)
    moderate = tour_df[
        (tour_df[mag_col] > 5.0) & (tour_df[mag_col] <= mag_ceiling)
    ].sort_values(mag_col)
    challenging = tour_df[
        (tour_df[mag_col] > mag_ceiling) & (tour_df[mag_col] <= challenge_ceiling)
    ].sort_values(mag_col)

## The filtered objects that come from our tour dataframe and then filtered further into difficulties 
## easy is anything mag 5 or brighter, moderate is beteween 5, and the mag ceiling set prior, and challenging is between the ceiliing and challenge ceiling of before
 
    # Build the tour with a mix of difficulties
    if level == "Beginner":
        tour_objects = (
            list(easy.index[:3]) +
            list(moderate.index[:4]) +
            (list(challenging.index[:1]) if include_challenge else [])
        )
    elif level == "Intermediate":
        tour_objects = (
            list(easy.index[:2]) +
            list(moderate.index[:7]) +
            list(challenging.index[:3])
        )
    else:
        tour_objects = (
            list(easy.index[:1]) +
            list(moderate.index[:5]) +
            list(challenging.index[:10])
        )
 
    tour_result = tour_df.loc[
        [i for i in tour_objects if i in tour_df.index]
    ].copy()

## Picks how many objects from each tier based on experience. Beginners get 3 easy, 4 mod, and 1 challenging ideally, we had some issues with it not fully loading all of them somtimes
## I've tried to figure out why it won't perfectly match up sometimes, or why it won't display the easy targets sometimes. I am still trying, if it doesn't work later either, I couldn't figure it out
## Int. has 2 easy, 7 mod, and 3 challenging! Adv. has 1 easy, 5 mod, and 10 challenging! It combines all of them up into one list 

    if tour_result.empty:
        st.warning("Could not generate a tour with the current settings.")
        return
 
    # Tour progress
    observed_in_tour = [
        n for n in tour_result[name_col].values if n in obs_log
    ]
    progress = len(observed_in_tour) / len(tour_result) if len(tour_result) > 0 else 0
    st.progress(
        progress,
        text=f"Tour progress: {len(observed_in_tour)} of {len(tour_result)} observed ({progress:.0%})"
    )

## This checks which tour objects have already been observed by comparing names with the observation log keys
## and again, I love a little percentage bar so I had to bring it back for the progress you make on your tour. It fills up by clicking observed on the object
 
    # Display the tour
    tour_num = 1
    prev_tier = None
 
    for idx, row in tour_result.iterrows():
        mag = row.get(mag_col, None)
        obj_name = row.get(name_col, "Unknown")
        is_observed = obj_name in obs_log
 
        # Determine tier
        if mag and mag <= 5.0:
            tier = "Start here — easiest targets"
            tier_icon = "🟢"
        elif mag and mag <= mag_ceiling:
            tier = "Main targets"
            tier_icon = "🔵"
        else:
            tier = "Challenge objects — push yourself!"
            tier_icon = "🟠"
 
        # Show tier header when it changes
        if tier != prev_tier:
            st.markdown(f"#### {tier_icon} {tier}")
            prev_tier = tier
 
## The tour object is sent through the if statements which determines the difficulty tier based on its magnitude
## the fun colors are included, easy is green, blue is main, and orange is challenging, it seems pretty obvious
## the prev tier tracker makes sure the same heading isn't printed twice in a row

        # Object card
        observed_marker = " ✓ Observed" if is_observed else ""
        obj_type = row.get('NormalizedType', 'Unknown')
        constellation = row.get(analytics.columns.get('CONSTELLATION', ''), 'Unknown')
        best_month = row.get('BestViewingMonth', 'Unknown')
        color = TYPE_COLORS.get(obj_type, '#888780')
 
        with st.expander(
            f"**{tour_num}. {obj_name}** — {obj_type} | "
            f"mag {mag:.1f} | {constellation}{observed_marker}"
        ):
            col1, col2 = st.columns([2, 1])
 
            with col1:
                # Observing tip
                tip = generate_observing_tip(row, mag_col, aperture, mag_limit)
                st.markdown(f"**Observing tip:** {tip}")
                st.caption(f"Best viewing: {best_month} | Size: {row.get('SizeCategory', 'Unknown')}")
 
                # Remarks from catalog
                remarks = row.get(analytics.columns.get('REMARKS', ''), '')
                if remarks and str(remarks).strip() and str(remarks) != 'nan':
                    st.markdown(f"**Catalog notes:** {remarks}")
 
            with col2:
                # Quick action buttons
                if not is_observed:
                    if st.button("Mark Observed", key=f"tour_obs_{obj_name}"):
                        obs_log[obj_name] = {
                            "date": datetime.now().strftime("%Y-%m-%d"),
                            "notes": f"Observed during {season} tour",
                        }
                        save_observation_log()
                        st.rerun()
                else:
                    st.success(f"Observed {obs_log[obj_name].get('date', '')}")
 
                favorites = profile.get_favorites()
                if obj_name not in favorites:
                    if st.button("Add Favorite", key=f"tour_fav_{obj_name}"):
                        profile.add_favorite(obj_name)
                        profile.save_profile()
                        st.rerun()
 
## this is a bit of a larger chunk. Each object gets a collapsible card with the header showing the name of the object, the type, the mag, its constellation and its checkmarked if its observed
## inside of the card in the left column (col1), we get the observing tip from a little bit ago, best viewing month, size
## in the right column (col2) we have buttons for 'mark observed' or a green 'observed' note if you've already seen it!
## like previously mentioned, we have a button to add to favorites if you so choose

        tour_num += 1
 
    # Tour summary
    st.divider()
    st.markdown("#### Tour Summary")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Objects", len(tour_result))
    col2.metric("Observed", len(observed_in_tour))
    col3.metric("Remaining", len(tour_result) - len(observed_in_tour))
 
    type_counts = tour_result['NormalizedType'].value_counts()
    type_summary = ", ".join([f"{count} {t}" for t, count in type_counts.items()])
    col4.metric("Mix", type_summary)
 
    # Variety check
    types_in_tour = tour_result['NormalizedType'].nunique()
    if types_in_tour >= 3:
        st.success("Great variety! Your tour includes galaxies, nebulae, and clusters.")
    elif types_in_tour >= 2:
        st.info("Good mix of object types in your tour.")
 
## At the very bottom of this tab, we added a couple metrics for completeness sake
## col1 prints how many objects there are in the tour, col2 prints how many the user has observed, col3 prints the remianing objects, and col4 describes the mix of objects
 
# ──────────────────────────────────────────────
# Chat Interface (placeholder for LLM tools)
# ──────────────────────────────────────────────
 
def chat_interface(profile):
    st.subheader("Observing Assistant")
    st.write(f"logged in as **{profile.get_preference('name') or 'Observer'}**") 
    
    # Create the trigger button 
 
    if st.button("Generate personalized plan"):
        with st.spinner("creating best plan for your equipment..."):
            user_data = profile.preferences
            plan = astro_ai.generate_observing_plan(user_data)

            st.divider
            st.markdown("###our Custom Star Guide")
            st.info(plan) 
## andrew's work for the LLM tools 
 
# ──────────────────────────────────────────────
# AstroStreamlitUI Class and Entrypoint
# ──────────────────────────────────────────────

class AstroStreamlitUI:

    def __init__(self):
        pass

    def run(self):
        st.set_page_config(
            page_title="Messier Object Tourist Guide",
            page_icon="🔭",
            layout="wide",
        )

        st.title("Messier Object Tourist Guide")
        st.caption("Your personalized deep-sky observing companion")

        with st.expander("Setting up your profile"):
            st.markdown(
                "This step is not super important, but if you want a more personalized "
                "star map, you can change your name, telescope aperture, experience level, "
                "and preferred season! If you do not have a telescope, these steps are not "
                "necessary to run this guide."
            )

        # Load data and profile
        analytics = load_messier_data()
        profile = get_user_profile()

        # Render sidebar (pass analytics for metrics)
        profile = render_sidebar(profile, analytics)

        # Main content tabs
        tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
            "Sky Chart",
            "Finder Chart",
            "Object Details",
            "Catalog Browser",
            "Your Observing Tour",
            "Observation Log",
            "Observing Assistant",
        ])

        with tab1:
            with st.expander("About this tab"):
                st.markdown(
                    "You can play around with this circular plot of the Messier objects. "
                    "Depending on your preferred season, you can choose to show only the "
                    "objects for that season. Depending on your telescope, you will see "
                    "which objects are visible. Last but not least! You can choose to view "
                    "the plot by object type or viewing difficulty. The position will not "
                    "change; only the key describing the points will."
                )
            display_polar_chart(analytics, profile)

        with tab2:
            with st.expander("About this tab"):
                st.markdown(
                    "Instead of a circular plot, this is a more traditional viewing of the "
                    "objects by their Right Ascension and their magnitude. The Finder Chart "
                    "is better at visualizing the magnitudes vs the RA values at a glance."
                )
            display_scatter_chart(analytics, profile)

        with tab3:
            with st.expander("About this tab"):
                st.markdown(
                    "You may select any object of your choosing to find info about its "
                    "magnitude, best month for viewing from your specified location, and "
                    "apparent angular size! There are a few extra notes outlining the "
                    "position in the sky and other tools."
                )
            col1, col2 = st.columns([1, 1])
            with col1:
                display_object_details(analytics, profile)
            with col2:
                display_favorites(analytics, profile)

        with tab4:
            with st.expander("About this tab"):
                st.markdown(
                    "The Catalog is a full table of all 110 objects, if combing through "
                    "1 by 1 is too much. You can filter this table by its type, max "
                    "magnitude, and season. The table shows a few facts about objects "
                    "similar to those in the Object Details section."
                )
            display_object_table(analytics, profile)

        with tab5:
            with st.expander("About this tab"):
                st.markdown(
                    "You have access to a custom observing plan for that night based on "
                    "the sidebar settings in your profile. Beginners have 8 objects, while "
                    "advanced observers have 16, with harder targets to find."
                )
            display_observing_tour(analytics, profile)

        with tab6:
            with st.expander("About this tab"):
                st.markdown(
                    "Similar to the Observing Tour, you can track objects that you want "
                    "to observe. However, the structure of the Tour is not there. It is "
                    "a marathon tracker; you add your observations and any notes on the "
                    "objects until you have all 110."
                )
            display_observation_log(analytics, profile)

        with tab7:
            chat_interface(profile)

## most all of this is either visualizing and putting the pieces together for the app
## The profile sidebar is rendered, along with adding titles are the app, the tabs, and i thought it would have been nice to add little descriptors for each tab and breifly what it does

# Entrypoint function for main.py
def run_streamlit_ui():
    ui = AstroStreamlitUI()
    ui.run()

## i can't believe we got this far! Last thing I promise
## this allows for all of this code to be wrapped up into one call function in main.py
## and now you have too created the app. 