"""
Configuration settings for the AI Agent Web Generator.
"""

from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class AppConfig:
    """Application configuration settings."""
    
    # API Settings
    API_BASE_URL: str = "http://localhost:8000"
    API_TIMEOUT: int = 300
    API_HEALTH_TIMEOUT: int = 5
    API_CONNECT_TIMEOUT: int = 10
    API_READ_TIMEOUT: int = 600
    

    

    
    # Framework Options
    FRAMEWORKS: List[str] = None
    STYLING_OPTIONS: List[str] = None
    FEATURE_OPTIONS: List[str] = None
    COMPLEXITY_OPTIONS: List[str] = None
    
    # UI Settings
    PAGE_TITLE: str = "AI Agent - Build Amazing Apps"
    PAGE_ICON: str = "🚀"
    LAYOUT: str = "centered"
    INITIAL_SIDEBAR_STATE: str = "collapsed"
    
    def __post_init__(self):
        """Initialize default values for lists."""

        
        if self.FRAMEWORKS is None:
            self.FRAMEWORKS = [
                "React", "Vue.js", "Vanilla JavaScript", 
                "Python Flask", "Python FastAPI"
            ]
        
        if self.STYLING_OPTIONS is None:
            self.STYLING_OPTIONS = [
                "Tailwind CSS", "Bootstrap", "CSS3", 
                "Material-UI", "Chakra UI"
            ]
        
        if self.FEATURE_OPTIONS is None:
            self.FEATURE_OPTIONS = [
                "User Authentication", "Responsive Design", "Database Integration",
                "API Integration", "Real-time Updates", "File Upload", 
                "Search Functionality", "Dark Mode", "Internationalization", 
                "Progressive Web App"
            ]
        
        if self.COMPLEXITY_OPTIONS is None:
            self.COMPLEXITY_OPTIONS = ["Simple", "Medium", "Complex"]


# Global configuration instance
app_config = AppConfig()


def get_config() -> AppConfig:
    """Get the application configuration."""
    return app_config


def get_custom_css() -> str:
    """Get custom CSS for the application."""
    return """
    <style>
        /* Modern gradient background - darker style */
        .main {
            background: linear-gradient(180deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
            min-height: 100vh;
        }
        
        /* Hide Streamlit default elements */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        /* Main container styling */
        .main .block-container {
            max-width: 1200px;
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        
        /* Modern typography */
        h1, h2, h3 {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            font-weight: 700;
            color: #ffffff;
        }
        
        /* Main title styling */
        .main h1 {
            font-size: 3.5rem;
            font-weight: 800;
            text-align: center;
            margin-bottom: 0.5rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        /* Subtitle styling */
        .main p {
            font-size: 1.2rem;
            text-align: center;
            color: #b0b0b0;
            margin-bottom: 0.5rem;
            font-weight: 400;
        }
        
        /* Text area styling */
        .stTextArea textarea {
            border-radius: 20px;
            border: 2px solid #2a2a3e;
            background: whitesmoke;
            backdrop-filter: blur(10px);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            font-size: 1rem;
            padding: 1.5rem;
            transition: all 0.3s ease;
            margin-bottom: 0;
        }
        
        .stTextArea textarea:focus {
            border-color: #4f46e5;
            box-shadow: 0 8px 32px rgba(79, 70, 229, 0.3);
            outline: none;
        }
        
        /* Remove background from text area container only */
        .stTextArea .st-bu {
            background: transparent !important;
        }
        
        /* Remove border from text area container */
        .st-emotion-cache-1om1ktf div {
            border-width: 0px !important;
        }
        
        /* Remove extra spacing around generation settings */
        .stMarkdown[data-testid="stMarkdown"] {
            margin: 0 !important;
            padding: 0 !important;
        }
        
        .st-emotion-cache-5rimss {
            margin: 0 !important;
            padding: 0 !important;
        }
        
        /* Image upload section styling */
        .image-upload-section {
            background: transparent;
            border-radius: 20px;
            padding: 0.5rem;
            margin: 1rem 0;
            backdrop-filter: blur(10px);
            border: 1px solid transparent;
            box-shadow: 0 8px 32px transparent;
        }
        
        .image-upload-section p {
            color: #b0b0b0;
            margin-bottom: 0.5rem;
        }

        .st-emotion-cache-fg4pbf {
            color: #b0b0b0;
        }
        
        /* File uploader styling */
        .stFileUploader > div {
            border-radius: 15px;
            border: 2px solid #2a2a3e;
            background: whitesmoke !important;
            backdrop-filter: blur(10px);
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
        }
        
        .stFileUploader > div:focus-within {
            border-color: #4f46e5;
            box-shadow: 0 4px 15px rgba(79, 70, 229, 0.3);
        }
        
        /* Image metadata fields styling */
        .image-upload-section h3 {
            color: #333;
            font-size: 1.2rem;
            font-weight: 600;
            margin-bottom: 1rem;
            padding: 0.5rem 0;
            border-bottom: 2px solid #667eea;
        }
        
        .image-upload-section strong {
            color: #b0b0b0;
            font-size: 0.9rem;
        }
        
        /* Expander styling */
        .streamlit-expanderHeader {
            background: rgba(255, 255, 255, 0.1) !important;
            border-radius: 15px !important;
            border: 2px solid rgba(255, 255, 255, 0.2) !important;
            color: #b0b0b0 !important;
            font-weight: 600 !important;
            padding: 0.55rem 1rem !important;
            margin: 0.5rem 0 !important;
            transition: all 0.3s ease !important;
        }
        
        .streamlit-expanderHeader:hover {
            background: rgba(255, 255, 255, 0.2) !important;
            border-color: rgba(102, 126, 234, 0.5) !important;
            transform: translateY(-1px) !important;
        }
        
        .streamlit-expanderContent {
            background: rgba(255, 255, 255, 0.05) !important;
            border-radius: 15px !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            margin-top: 0.5rem !important;
            padding: 1rem !important;
        }
        
        .image-upload-section .stTextInput > div > div {
            border-radius: 10px;
            border: 2px solid #e5e7eb;
            background: white !important;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }
        
        .image-upload-section .stTextInput > div > div:focus-within {
            border-color: #667eea;
            box-shadow: 0 2px 8px rgba(102, 126, 234, 0.2);
        }
        
        .image-upload-section .stTextArea > div > div {
            border-radius: 10px;
            border: 2px solid #e5e7eb;
            background: white !important;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }
        
        .image-upload-section .stTextArea > div > div:focus-within {
            border-color: #667eea;
            box-shadow: 0 2px 8px rgba(102, 126, 234, 0.2);
        }
        
        .image-upload-section .stSelectbox > div > div {
            border-radius: 10px;
            border: 2px solid #e5e7eb;
            background: white !important;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }
        
        .image-upload-section .stSelectbox > div > div:focus-within {
            border-color: #667eea;
            box-shadow: 0 2px 8px rgba(102, 126, 234, 0.2);
        }
        
        /* Button styling */
        .stButton > button {
            border-radius: 50px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border: none;
            color: white;
            font-weight: 600;
            padding: 0.5rem 2rem;
            font-size: 1rem;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
            width: auto;
            min-width: 200px;
            height: auto;
        }
        
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(102, 126, 234, 0.5);
            background: linear-gradient(135deg, #5a67d8 0%, #6b46c1 100%);
        }
        
        /* Selectbox styling */
        .stSelectbox > div > div {
            border-radius: 15px;
            border: 2px solid #2a2a3e;
            background: whitesmoke !important;
            backdrop-filter: blur(10px);
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
        }
        
        .stSelectbox > div > div:focus-within {
            border-color: #4f46e5;
            box-shadow: 0 4px 15px rgba(79, 70, 229, 0.3);
        }
        
        /* Ensure selectbox background is always whitesmoke */
        .stSelectbox .st-bw {
            background: whitesmoke !important;
        }
        
        
        /* Multiselect styling */
        .stMultiSelect > div > div {
            border-radius: 15px;
            border: 2px solid #2a2a3e;
            background: whitesmoke !important;
            backdrop-filter: blur(10px);
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
        }
        
        .stMultiSelect > div > div:focus-within {
            border-color: #4f46e5;
            box-shadow: 0 4px 15px rgba(79, 70, 229, 0.3);
        }
        
        /* Ensure multiselect background is always whitesmoke */
        .stMultiSelect .st-bw {
            background: whitesmoke !important;
        }
        
        /* Tabs styling */
        .stTabs [data-baseweb="tab-list"] {
            gap: 1rem;
            background: rgba(255, 255, 255, 0.9);
            border-radius: 15px;
            padding: 0.5rem;
            backdrop-filter: blur(10px);
        }
        
        .stTabs [data-baseweb="tab"] {
            border-radius: 10px;
            background: transparent;
            color: #333;
            font-weight: 500;
            transition: all 0.3s ease;
        }
        
        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        }
        
        /* Preview container */
        .preview-container {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            padding: 1.5rem;
            margin: 1rem 0;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.3);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        }
        
        /* Code editor */
        .code-editor {
            background: rgba(30, 30, 30, 0.9);
            border-radius: 15px;
            padding: 1rem;
            font-family: 'JetBrains Mono', 'Fira Code', monospace;
            color: #e1e5e9;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        /* Metrics styling */
        .metric-container {
            background: rgba(255, 255, 255, 0.9);
            border-radius: 15px;
            padding: 1rem;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.3);
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
        }
        
        /* Success/Error messages */
        .stSuccess {
            background: rgba(34, 197, 94, 0.1);
            border-radius: 10px;
            border: 1px solid rgba(34, 197, 94, 0.3);
        }
        
        .stError {
            background: rgba(239, 68, 68, 0.1);
            border-radius: 10px;
            border: 1px solid rgba(239, 68, 68, 0.3);
        }
        
        /* Loading spinner */
        .stSpinner > div {
            border-color: #667eea;
        }
        
        /* Custom scrollbar */
        ::-webkit-scrollbar {
            width: 8px;
        }
        
        ::-webkit-scrollbar-track {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: linear-gradient(135deg, #5a67d8 0%, #6b46c1 100%);
        }
    </style>
    """
