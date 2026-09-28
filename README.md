# example1

def render_location_asset(title, status, locations):
    """Render one asset/location block using native Streamlit components."""

    status_text = availability_status(status)
    number_locations = len(locations)

    if number_locations == 1:
        location_label = "1 location"
    else:
        location_label = f"{number_locations} locations"

    # -------------------------------------------------------------------------
    # Asset summary
    # -------------------------------------------------------------------------

    col1, col2 = st.columns([5, 1])

    with col1:
        st.markdown(f"**{title}**")
        st.caption(location_label)

    with col2:
        st.markdown(f"**{status_text}**")

    # -------------------------------------------------------------------------
    # Location details
    # -------------------------------------------------------------------------

    if locations:

        if number_locations == 1:
            expander_label = f"View 1 {title} location"
        else:
            expander_label = f"View {number_locations} {title} locations"

        with st.expander(expander_label):
            render_location_list(locations)

    else:
        st.caption("No location registered.")

    st.markdown("")
