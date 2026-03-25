"""
AstroStreamlitUI
----------------
Streamlit-based user interface for the Messier Object Tourist Guide app.

Classes:
    AstroStreamlitUI

Methods:
    render_sidebar(user_profile):
        # Display user profile settings in sidebar
        pass
    display_star_chart(analytics_engine):
        # Plot Messier objects using matplotlib
        pass
    chat_interface(llm_tools):
        # Textbox for user to interact with LLM tools
        pass

 
Provides:
    - Sidebar for user profile settings (aperture, location, experience, season)
    - Polar sky chart (Matplotlib polar plot of Messier objects by RA/Dec)
    - Scatter finder chart (RA vs Magnitude)
    - Filterable data table of Messier objects
    - Object detail cards with full stats
    - Observation log to track observed objects with dates and notes
    - Favorites management
    - Chat interface placeholder (for LLM tools integration)
"""
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
 
 
# ──────────────────────────────────────────────
# Data Loading (cached so it only runs once)
# ──────────────────────────────────────────────
 
@st.cache_data
def load_messier_data():
    """Download, parse, and clean the Messier catalog. Cached across reruns."""
    ingester = MessierDataIngester()
    csv_path = ingester.fetch_and_save()
    objects = ingester.parse_messier_objects_to_dict(csv_path)
    analytics = AstroAnalyticsEngine(objects)
    analytics.clean_data()
    return analytics
 
 
def get_user_profile():
    """Load or initialize user profile in session state."""
    if "profile" not in st.session_state:
        st.session_state.profile = UserProfile()
    return st.session_state.profile
 
 
# ──────────────────────────────────────────────
# Observation Log — Persistence
# ──────────────────────────────────────────────
 
def load_observation_log():
    """Load the observation log from disk into session state."""
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
    """Save the current observation log to disk."""
    try:
        with open(OBSERVATION_LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(st.session_state.obs_log, f, indent=2)
    except IOError as e:
        st.error(f"Could not save observation log: {e}")
 
 
# ──────────────────────────────────────────────
# Sidebar — User Profile Settings
# ──────────────────────────────────────────────
 
def render_sidebar(profile, analytics):
    """Display and manage user profile settings in the sidebar."""
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
 
 
# ──────────────────────────────────────────────
# Polar Sky Chart
# ──────────────────────────────────────────────
 
def display_polar_chart(analytics, profile):
    """
    Circular sky chart showing Messier objects plotted by Right Ascension
    (angle) and Magnitude (radius). Mimics an all-sky view where brighter
    objects are closer to the center.
    """
    st.subheader("Sky Chart")
    st.caption(
        "A polar view of all Messier objects. Angle = Right Ascension, "
        "distance from center = magnitude (brighter objects are closer to center)."
    )
 
    aperture = profile.get_preference("aperture_mm") or DEFAULT_APERTURE_MM
    season = profile.get_preference("preferred_season") or "Spring"
    mag_col = analytics.columns['MAGNITUDE']
    name_col = analytics.columns['NAME']
    mag_limit = analytics.aperture_mag_limit(aperture)
 
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
 
 
# ──────────────────────────────────────────────
# Scatter Finder Chart
# ──────────────────────────────────────────────
 
def display_scatter_chart(analytics, profile):
    """
    Scatter plot of Messier objects: RA vs Magnitude.
    Traditional finder chart view.
    """
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
 
 
# ──────────────────────────────────────────────
# Object Detail Cards
# ──────────────────────────────────────────────
 
def display_object_details(analytics, profile):
    """Show detailed info card for a selected Messier object."""
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
 
    # Remarks
    remarks = row.get(remarks_col, "")
    if remarks and str(remarks).strip() and str(remarks) != "nan":
        st.markdown("**Notes**")
        st.info(str(remarks))
 
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
 
 
# ──────────────────────────────────────────────
# Data Table with Filters
# ──────────────────────────────────────────────
 
def display_object_table(analytics, profile):
    """Show a filterable table of Messier objects."""
    st.subheader("Catalog Browser")
 
    aperture = profile.get_preference("aperture_mm") or DEFAULT_APERTURE_MM
    mag_col = analytics.columns['MAGNITUDE']
    name_col = analytics.columns['NAME']
    type_col = analytics.columns['TYPE']
 
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
 
    df = analytics.get_all_objects().copy()
 
    if selected_type != "All":
        df = df[df['NormalizedType'] == selected_type]
 
    df = df[df[mag_col] <= max_mag]
 
    if selected_season != "All":
        seasonal = analytics.get_visible_in_season(selected_season)
        df = df[df.index.isin(seasonal.index)]
 
    # Add visibility info
    mag_limit = analytics.aperture_mag_limit(aperture)
    df['Visible'] = df[mag_col].apply(
        lambda m: "Yes" if m <= mag_limit else "No"
    )
 
    # Add observed status
    obs_log = load_observation_log()
    df['Observed'] = df[name_col].apply(
        lambda n: "Yes" if n in obs_log else ""
    )
 
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
 
 
# ──────────────────────────────────────────────
# Observation Log
# ──────────────────────────────────────────────
 
def display_observation_log(analytics, profile):
    """Track which Messier objects the user has observed, with dates and notes."""
    st.subheader("Observation Log")
 
    name_col = analytics.columns['NAME']
    mag_col = analytics.columns['MAGNITUDE']
    type_col = analytics.columns['TYPE']
 
    obs_log = load_observation_log()
 
    # Progress bar
    progress = len(obs_log) / 110
    st.progress(progress, text=f"{len(obs_log)} of 110 Messier objects observed ({progress:.0%})")
 
    # Add new observation
    st.markdown("#### Log a New Observation")
 
    observed_names = list(obs_log.keys())
    unobserved = sorted([
        n for n in analytics.df[name_col].dropna().unique()
        if n not in observed_names
    ])
 
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
 
    # Display log
    if obs_log:
        st.markdown("#### Your Observations")
 
        # Sort by date (most recent first)
        sorted_log = sorted(
            obs_log.items(),
            key=lambda x: x[1].get("date", ""),
            reverse=True,
        )
 
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
    else:
        st.info(
            "No observations logged yet. Select an object above "
            "to start tracking your Messier marathon!"
        )
 
 
# ──────────────────────────────────────────────
# Favorites
# ──────────────────────────────────────────────
 
def display_favorites(analytics, profile):
    """Manage and display favorite Messier objects."""
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
 
 
# ──────────────────────────────────────────────
# Observing Tour — Equipment-Based Custom Tours
# ──────────────────────────────────────────────
 
def generate_observing_tip(row, mag_col, aperture, mag_limit):
    """Generate a short data-driven observing tip for a Messier object."""
    mag = row.get(mag_col, None)
    obj_type = row.get('NormalizedType', 'Unknown')
    size_cat = row.get('SizeCategory', 'Unknown')
    name = row.get('Name', 'This object')
 
    tips = []
 
    # Brightness-based tip
    if mag and mag <= 3.0:
        tips.append("Visible to the naked eye even in cities.")
    elif mag and mag <= 5.0:
        tips.append("Naked eye target under dark skies.")
    elif mag and mag <= 8.5:
        tips.append("Best with binoculars or a small scope.")
    elif mag and mag <= mag_limit:
        tips.append(f"Requires your telescope ({aperture:.0f}mm).")
 
    # Size-based tip
    if size_cat == "Very Large":
        tips.append("Very large — use low magnification for the best view.")
    elif size_cat == "Large":
        tips.append("Large target — fits well in a wide-field eyepiece.")
    elif size_cat == "Small":
        tips.append("Compact — try higher magnification to see detail.")
 
    # Type-based tip
    if obj_type == "Galaxy":
        tips.append("Look for a faint fuzzy glow. Averted vision helps.")
    elif obj_type == "Nebula":
        tips.append("A nebula filter can improve contrast significantly.")
    elif obj_type == "Cluster":
        tips.append("Star cluster — should resolve into individual stars.")
 
    return " ".join(tips) if tips else "Point your telescope and enjoy the view!"
 
 
def display_observing_tour(analytics, profile):
    """
    Generate a custom observing tour based on the user's equipment,
    experience level, and preferred season. Pure data-driven — no LLM needed.
    """
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
 
    # Split into difficulty tiers
    easy = tour_df[tour_df[mag_col] <= 5.0].sort_values(mag_col)
    moderate = tour_df[
        (tour_df[mag_col] > 5.0) & (tour_df[mag_col] <= mag_ceiling)
    ].sort_values(mag_col)
    challenging = tour_df[
        (tour_df[mag_col] > mag_ceiling) & (tour_df[mag_col] <= challenge_ceiling)
    ].sort_values(mag_col)
 
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
 
 
# ──────────────────────────────────────────────
# Chat Interface (placeholder for LLM tools)
# ──────────────────────────────────────────────
 
def chat_interface():
    """
    Placeholder chat interface.
    Will be connected to AstroLLMTools once that class is implemented.
    """
    st.subheader("Observing Assistant")
    st.info(
        "The AI observing assistant will be available once the LLM tools "
        "are connected. For now, explore the catalog using the other tabs!"
    )
 
    with st.expander("Coming soon — AI features"):
        st.markdown(
            "- Ask about any Messier object and get its discovery story\n"
            "- Get a personalized observing plan for tonight\n"
            "- Observing tips based on your experience level and equipment\n"
            "- Custom seasonal viewing guides"
        )
 
 
# ──────────────────────────────────────────────
# Main App Layout
# ──────────────────────────────────────────────
 
def main():
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
        "Catalog Explorer",
        "Observing Tour",
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
        chat_interface()
 
 
if __name__ == "__main__":
    main()