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
import numpy as np
 
from messier_data_ingester import MessierDataIngester
from astro_analytics_engine import AstroAnalyticsEngine
from user_profile import UserProfile, VALID_EXPERIENCE_LEVELS, VALID_SEASONS
from constants import DEFAULT_APERTURE_MM
 
 
# ──────────────────────────────────────────────
# Data loading (cached so it only runs once)
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
# Sidebar — User Profile Settings
# ──────────────────────────────────────────────
 
def render_sidebar(profile):
    """Display and manage user profile settings in the sidebar."""
    st.sidebar.title("Observer Profile")
 
    # Name
    name = st.sidebar.text_input(
        "Your Name",
        value=profile.get_preference("name") or ""
    )
    if name != profile.get_preference("name"):
        profile.update_preferences("name", name)
 
    # Location
    location = st.sidebar.text_input(
        "Location",
        value=profile.get_preference("location") or "Columbus"
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
 
    # Show current profile summary
    st.sidebar.divider()
    st.sidebar.caption(str(profile))
 
    return profile
 
 
# ──────────────────────────────────────────────
# Finder Chart — Matplotlib Scatter Plot
# ──────────────────────────────────────────────
 
def display_star_chart(analytics, profile):
    """
    Plot Messier objects as a scatter plot.
    X-axis: Right Ascension (hours), Y-axis: Magnitude (inverted, brighter on top).
    Color-coded by object type, sized by apparent size.
    """
    st.subheader("Finder Chart")
 
    aperture = profile.get_preference("aperture_mm") or DEFAULT_APERTURE_MM
    season = profile.get_preference("preferred_season") or "Spring"
 
    # Filter options
    col1, col2 = st.columns(2)
    with col1:
        show_season_only = st.checkbox(f"Show only {season} objects", value=False)
    with col2:
        show_visible_only = st.checkbox("Show only visible with my telescope", value=False)
 
    # Start with full dataset
    df = analytics.get_all_objects().copy()
 
    # Apply filters
    if show_season_only:
        seasonal = analytics.get_visible_in_season(season)
        df = df[df.index.isin(seasonal.index)]
 
    if show_visible_only:
        visible = analytics.filter_by_aperture_and_brightness(aperture)
        df = df[df.index.isin(visible.index)]
 
    # Need RA_Decimal and Magnitude for plotting
    mag_col = analytics.columns['MAGNITUDE']
    name_col = analytics.columns['NAME']
 
    plot_df = df.dropna(subset=['RA_Decimal', mag_col]).copy()
 
    if plot_df.empty:
        st.warning("No objects match the current filters.")
        return
 
    # Color map by normalized type
    type_colors = {
        "Galaxy": "#7F77DD",
        "Nebula": "#1D9E75",
        "Cluster": "#D85A30",
        "Other": "#888780",
    }
 
    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_alpha(0.0)
    ax.set_facecolor("none")
 
    for obj_type, color in type_colors.items():
        subset = plot_df[plot_df['NormalizedType'] == obj_type]
        if subset.empty:
            continue
 
        # Size dots by apparent size (bigger objects = bigger dots)
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
 
    # Invert Y axis (brighter = lower magnitude = higher on chart)
    ax.invert_yaxis()
    ax.set_xlabel("Right Ascension (hours)", fontsize=12)
    ax.set_ylabel("Magnitude (brighter ↑)", fontsize=12)
    ax.set_xlim(0, 24)
    ax.legend(loc="upper right", fontsize=9)
    ax.grid(True, alpha=0.3)
    ax.tick_params(colors="gray")
    ax.xaxis.label.set_color("gray")
    ax.yaxis.label.set_color("gray")
 
    # Season shading
    from constants import SEASON_RA
    ra_min, ra_max = SEASON_RA.get(season, (0, 24))
    if ra_min < ra_max:
        ax.axvspan(ra_min, ra_max, alpha=0.08, color="#1D9E75",
                   label=f"{season} RA range")
    else:
        ax.axvspan(ra_min, 24, alpha=0.08, color="#1D9E75")
        ax.axvspan(0, ra_max, alpha=0.08, color="#1D9E75")
 
    st.pyplot(fig)
    plt.close(fig)
 
    st.caption(
        f"Showing {len(plot_df)} objects. "
        f"Dot size reflects apparent angular size. "
        f"Green shading = {season} RA range."
    )
 
 
# ──────────────────────────────────────────────
# Data Table with Filters
# ──────────────────────────────────────────────
 
def display_object_table(analytics, profile):
    """Show a filterable table of Messier objects with favorites toggle."""
    st.subheader("Messier Catalog Explorer")
 
    aperture = profile.get_preference("aperture_mm") or DEFAULT_APERTURE_MM
    mag_col = analytics.columns['MAGNITUDE']
    name_col = analytics.columns['NAME']
    type_col = analytics.columns['TYPE']
 
    # Filter controls
    col1, col2, col3 = st.columns(3)
 
    with col1:
        types = ["All"] + sorted(analytics.df['NormalizedType'].dropna().unique().tolist())
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
 
    # Build filtered dataframe
    df = analytics.get_all_objects().copy()
 
    if selected_type != "All":
        df = df[df['NormalizedType'] == selected_type]
 
    df = df[df[mag_col] <= max_mag]
 
    if selected_season != "All":
        seasonal = analytics.get_visible_in_season(selected_season)
        df = df[df.index.isin(seasonal.index)]
 
    # Add visibility rating for the user's aperture
    mag_limit = analytics.aperture_mag_limit(aperture)
    df['Visible'] = df[mag_col].apply(
        lambda m: "Yes" if m <= mag_limit else "No"
    )
 
    # Select display columns
    display_cols = [
        name_col, type_col, mag_col,
        'NormalizedType', 'BestViewingMonth',
        'ApparentSizeAvg', 'SizeCategory', 'Visible'
    ]
    display_cols = [c for c in display_cols if c in df.columns]
 
    st.dataframe(
        df[display_cols].reset_index(drop=True),
        use_container_width=True,
        height=400,
    )
 
    st.caption(f"Showing {len(df)} objects. Visibility based on {aperture}mm aperture.")
 
    # ── Favorites Section ──
    st.subheader("Favorites")
 
    available_names = sorted(analytics.df[name_col].dropna().unique().tolist())
    favorites = profile.get_favorites()
 
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
            st.info("No favorites yet. Add some from the dropdown!")
 
    if favorites:
        fav_df = analytics.df[analytics.df[name_col].isin(favorites)]
        fav_display = [c for c in [name_col, type_col, mag_col, 'BestViewingMonth', 'SizeCategory'] if c in fav_df.columns]
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
        "are connected. For now, explore the catalog using the filters "
        "and finder chart above!"
    )
 
    # Show a preview of what the chat will do
    with st.expander("Coming soon — AI features"):
        st.markdown(
            "- Ask about any Messier object and get its discovery story\n"
            "- Get a personalized observing plan for tonight\n"
            "- Observing tips based on your experience level and equipment\n"
            "- Custom seasonal guides"
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
 
    # Render sidebar
    profile = render_sidebar(profile)
 
    # Main content tabs
    tab1, tab2, tab3 = st.tabs([
        "Finder Chart",
        "Catalog Explorer",
        "Observing Assistant",
    ])
 
    with tab1:
        display_star_chart(analytics, profile)
 
    with tab2:
        display_object_table(analytics, profile)
 
    with tab3:
        chat_interface()
 
 
if __name__ == "__main__":
    main()
