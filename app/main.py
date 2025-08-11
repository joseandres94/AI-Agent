import streamlit as st
import sys
import os

# Add the project root to the Python path for proper imports
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from app.utils.config import get_config, get_custom_css
    from app.utils.ui_components import create_main_content, create_results_display
except ImportError:
    # Fallback import if app module is not found
    from utils.config import get_config, get_custom_css
    from utils.ui_components import create_main_content, create_results_display

def initialize_session_state():
    """Initialize Streamlit session state variables."""
    config = get_config()

    if "generated_files" not in st.session_state:
        st.session_state.generated_files = {}

    if "preview_html" not in st.session_state:
        st.session_state.preview_html = ""

    if "generation_config" not in st.session_state:
        st.session_state.generation_config = {}
    if "rebuild_preview" not in st.session_state:
        st.session_state.rebuild_preview = False

def setup_page_config():
    """Setup the page configuration."""
    config = get_config()
    st.set_page_config(
        page_title=config.PAGE_TITLE,
        page_icon=config.PAGE_ICON,
        layout=config.LAYOUT,
        initial_sidebar_state=config.INITIAL_SIDEBAR_STATE
    )

def apply_custom_css():
    """Apply custom CSS to the application."""
    st.markdown(get_custom_css(), unsafe_allow_html=True)

def main():
    """Main Streamlit application."""
    
    # Initialize session state FIRST, before any UI components
    initialize_session_state()
    
    # Setup
    setup_page_config()
    apply_custom_css()
    
    # Add space above the title to center it
    st.markdown("<br><br><br><br><br>", unsafe_allow_html=True)
    
    # Header
    st.title("Build something Amazing")
    st.markdown("Create web applications by chatting with AI (Powered by GPT-5)")
    
    # Create main content
    create_main_content()
    
    # Create results display
    create_results_display()

if __name__ == "__main__":
    main() 