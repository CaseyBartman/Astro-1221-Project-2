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
    - Finder chart (Matplotlib scatter plot of Messier objects by RA/magnitude)
    - Filterable data table of Messier objects
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
 
    # Aperture
    aperture = st.sidebar.number_input(
        "Telescope Aperture (mm)",
        min_value=1.0,
        max_value=1000.0,
        value=float(profile.get_preference("aperture_mm") or DEFAULT_APERTURE_MM),
        step=1.0,
    )
    if aperture != profile.get_preference("aperture_mm"):
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
 
    # Filter controls
    col1, col2 = st.columns(2)
    with col1:
        show_season_only = st.checkbox(
            f"Show only {season} objects", value=False, key="polar_season"
        )
    with col2:
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
 
    # Plot objects by type
    for obj_type, color in TYPE_COLORS.items():
        mask = plot_df['NormalizedType'] == obj_type
        if not mask.any():
            continue
 
        sizes = plot_df.loc[mask, 'ApparentSizeAvg'].fillna(3).clip(lower=1)
        sizes = (sizes / sizes.max()) * 150 + 25
 
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
    mag_limit = analytics.aperture_mag_limit(aperture)
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
    mag_limit = analytics.aperture_mag_limit(aperture)
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
 
    # Load data and profile
    analytics = load_messier_data()
    profile = get_user_profile()
 
    # Render sidebar (pass analytics for metrics)
    profile = render_sidebar(profile, analytics)
 
    # Main content tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "Sky Chart",
        "Finder Chart",
        "Object Details",
        "Catalog Explorer",
        "Observation Log",
        "Observing Assistant",
    ])
 
    with tab1:
        display_polar_chart(analytics, profile)
 
    with tab2:
        display_scatter_chart(analytics, profile)
 
    with tab3:
        col1, col2 = st.columns([1, 1])
        with col1:
            display_object_details(analytics, profile)
        with col2:
            display_favorites(analytics, profile)
 
    with tab4:
        display_object_table(analytics, profile)
 
    with tab5:
        display_observation_log(analytics, profile)
 
    with tab6:
        chat_interface()
 
 
if __name__ == "__main__":
    main()