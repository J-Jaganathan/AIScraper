import streamlit as st

def hide_streamlit_sidebar():
    """
    Completely hide Streamlit's default sidebar and navigation elements
    This prevents the sidebar flash and removes all traces of the default navigation
    """
    st.markdown("""
        <style>
        /* Hide the entire sidebar */
        [data-testid="stSidebar"] {
            display: none !important;
        }
        
        /* Hide sidebar navigation */
        [data-testid="stSidebarNav"] {
            display: none !important;
        }
        
        /* Hide the collapsed sidebar control (hamburger menu) */
        [data-testid="collapsedControl"] {
            display: none !important;
        }
        
        /* Hide sidebar toggle button */
        button[data-testid="baseButton-header"] {
            display: none !important;
        }
        
        /* Ensure main content takes full width */
        .main .block-container {
            padding-left: 1rem !important;
            padding-right: 1rem !important;
            max-width: 100% !important;
        }
        
        /* Hide any residual sidebar elements */
        section[data-testid="stSidebar"] > div {
            display: none !important;
        }
        
        /* Remove sidebar spacing from main content */
        .main {
            margin-left: 0 !important;
        }
        
        /* Hide streamlit menu and footer */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        </style>
    """, unsafe_allow_html=True)

def apply_custom_styling():
    """
    Apply custom styling for the app
    """
    st.markdown("""
        <style>
        /* Custom app styling */
        .stApp {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        
        /* Card styling for forms */
        .form-card {
            background: white;
            padding: 2rem;
            border-radius: 15px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            margin: 2rem 0;
        }
        
        /* Button styling */
        .stButton > button {
            border-radius: 25px;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        }
        </style>
    """, unsafe_allow_html=True)