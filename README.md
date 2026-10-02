# example1

import streamlit as st
import os
from glob import glob
import yaml
from pydoc import importfile
from dotenv import load_dotenv

load_dotenv()

STATIC_DIR = "./structure/"
SIDEBAR_STRUCTURE = yaml.safe_load(open("sidebar_structure.yaml", "r"))

st.set_page_config(
    page_title="Thea Dashboard",
    page_icon="📊",
    layout="wide",
)

# Custom CSS injection
st.markdown(
    """
    <style>
    .st-emotion-cache-z5fcl4 {
        padding-top: 1rem;
    }
    .st-emotion-cache-195tgdc, .st-emotion-cache-le5x6g, 
    .st-emotion-cache-bijvfy, .st-emotion-cache-14uwc23 {
        gap: 0px;
    }
    .st-emotion-cache-1o1eenq p {
        margin-bottom: 0px;
        margin-top: 1rem;
    }
    button[kind="secondary"] {
        background: none !important;
        border: none;
        padding: 0!important;
        text-decoration: none;
        cursor: pointer;
        border: none !important;
        width: 100%;
        justify-content: left;
    }
    button[kind="secondary"]:hover {
        text-decoration: none;
    }
    button[kind="secondary"]:focus {
        outline: none !important;
        box-shadow: none !important;
    }
    .element-container:has(.logout-marker) + .element-container button {
        position: fixed !important;
        left: 1rem !important;
        bottom: 0.5rem !important;
        border: none !important;
        background: none !important;
        color: #63759a !important;
    }
    .element-container:has(iframe[height="0"]) {
        display: none;
     }
    </style>
    """,
    unsafe_allow_html=True,
)


def render_python(py_path: str) -> None:
    """
    Executes streamlit code from path by importing the script
    """
    _ = importfile(py_path)


def render_markdown(md_path: str) -> None:
    """
    Parse markdown file to include images and render in streamlit
    """
    dir_path = os.path.dirname(md_path)
    with open(md_path, "r") as f:
        lines = f.readlines()
        # Create an empty buffer list to temporarily store the lines of markdown file
        buffer = []
        # Use the glob library to search for image files
        images = []
        for ext in ("*.png", "*.jpg"):
            images.extend(glob(os.path.join(dir_path, ext)))
        images = [os.path.basename(x) for x in images]

    for line in lines:
        buffer.append(line)
        # Check if any images are present in the current line
        for image in images:
            # If an image is found, display the buffer list up to the last line
            if image in line:
                st.markdown("".join(buffer[:-1]), unsafe_allow_html=True)
                st.image(os.path.join(dir_path, image))
                buffer.clear()

    # Combine buffer to display the rest of markdown text
    st.markdown("".join(buffer), unsafe_allow_html=True)


def recursively_render_files(dir_path: str, sidebar_tree: dict) -> None:
    """
    Renders markdown and python files in a given directory recursively
    """
    # Stops recursion if python exists in current path
    py_files = glob(os.path.join(dir_path, "*.py"))
    if py_files:
        render_python(py_files[0])  # Render first file it finds
        return

    # Stops recursion if markdown exists in current path
    md_files = glob(os.path.join(dir_path, "*.md"))
    if md_files:
        render_markdown(md_files[0])  # Render first file it finds
        return

    if not sidebar_tree:
        st.error(f"No python or markdown file found in {dir_path}", icon="🚨")
        return

    # Iterate directories and continue recursion
    dir_names = list(sidebar_tree.keys())
    tabs = st.tabs(dir_names)
    for tab, name in zip(tabs, dir_names):
        with tab:
            recursively_render_files(os.path.join(dir_path, name), sidebar_tree[name])


def layout() -> None:
    """
    Dynamically changes the main section of the app based on what user clicks in sidebar
    """
    dir_path = st.session_state.get("dir_path")
    if dir_path:
        st.caption(f"## {st.session_state['project']} - {st.session_state['section']}")
        recursively_render_files(
            dir_path,
            SIDEBAR_STRUCTURE[st.session_state["project"]][st.session_state["section"]],
        )
    elif st.session_state.get("show_auth"):
        from utils.authenticate import logout

        logout()
    else:
        # Home page
        st.markdown("# Thea Dashboard")
        st.markdown("### Current projects")
        st.markdown(
            "\n".join([f"- {k}" for k in SIDEBAR_STRUCTURE.keys() if k != "Configure"])
        )


def sidebar() -> None:
    """
    Creates the sidebar structure from a yaml file
    """
    with st.sidebar:
        if st.button(":house: Home", type="secondary"):
            st.session_state["dir_path"] = False
            st.session_state["show_auth"] = False
        for project, sections in SIDEBAR_STRUCTURE.items():
            # Skip section from loading if not authenticated
            if project == "Configure" and not st.session_state.get("authenticated"):
                continue
            with st.expander(f"**{project}**"):
                for section in sections:
                    dir_path = os.path.join(STATIC_DIR, project, section)
                    if st.button(section, key=dir_path, type="secondary"):
                        st.session_state["dir_path"] = dir_path
                        st.session_state["section"] = section
                        st.session_state["project"] = project
                        st.session_state["show_auth"] = False
        st.markdown('<span class="logout-marker"></span>', unsafe_allow_html=True)
        if st.button("Logout", key="logout_btn", type="primary"):
            st.session_state["dir_path"] = False
            st.session_state["show_auth"] = True


def main():
    sidebar()
    layout()


if __name__ == "__main__":
    main()
