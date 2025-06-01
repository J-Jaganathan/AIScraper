import streamlit as st
import sys
import os
from utils.auth_utils import check_authentication, init_session_state, logout_user

# Configure page
st.set_page_config(
    page_title="AI Web Scraper",
    page_icon="🕷️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
init_session_state()

# Custom CSS
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(90deg, #FF6B6B, #4ECDC4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 3rem;
        font-weight: bold;
        margin-bottom: 2rem;
    }
    
    .feature-card {
        padding: 1.5rem;
        border-radius: 10px;
        border: 1px solid #e0e0e0;
        margin: 1rem 0;
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    
    .hero-section {
        text-align: center;
        padding: 3rem 0;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 15px;
        margin: 2rem 0;
    }
    
    .stats-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        text-align: center;
        margin: 1rem 0;
    }
    
    .sidebar-info {
        background: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

def show_landing_page():
    """Show landing page for non-authenticated users"""
    
    # Hero Section
    st.markdown("""
    <div class="hero-section">
        <h1>🕷️ AI-Powered Web Scraper</h1>
        <h3>Scrape any website with natural language prompts</h3>
        <p>Extract data from JavaScript-heavy sites like Amazon, Flipkart, and Government portals</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Features
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="feature-card">
            <h4>🤖 AI-Powered</h4>
            <p>Use natural language to describe what you want to scrape. No coding required!</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-card">
            <h4>🛡️ Stealth Mode</h4>
            <p>Advanced anti-detection techniques to bypass captchas and rate limiting.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="feature-card">
            <h4>📊 Rich Exports</h4>
            <p>Get your data as tables, CSV, Excel files, and interactive charts.</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Example prompts
    st.markdown("### 💡 Example Prompts")
    
    examples = [
        "Scrape top 50 mobiles from Flipkart with price, rating, and discount",
        "Get 100 laptops from Amazon with specifications and reviews",
        "Extract government tenders from ministry portal",
        "Scrape product reviews from e-commerce site"
    ]
    
    for example in examples:
        st.markdown(f"• *{example}*")
    
    # Authentication buttons in main area
    st.markdown("---")
    st.markdown("### 🚀 Get Started")
    
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("🔐 Login", use_container_width=True, type="primary"):
            st.session_state.show_page = "login"
            st.rerun()
    
    with col2:
        if st.button("📝 Sign Up", use_container_width=True):
            st.session_state.show_page = "signup"
            st.rerun()
    
    with col3:
        st.button("👨‍💼 Admin Login", use_container_width=True, disabled=True, 
                 help="Contact administrator for admin access")

def show_navigation():
    """Show navigation sidebar for authenticated users"""
    
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"**Welcome, {st.session_state.user['username']}!**")
    
    # Navigation menu
    menu_options = ["🏠 Dashboard", "📊 My Scrapes", "⚙️ Settings"]
    
    if st.session_state.user.get('is_admin', False):
        menu_options.extend(["👥 All Users", "📈 All Scrapes"])
    
    selected = st.sidebar.selectbox("Navigate to:", menu_options)
    
    # Handle navigation
    if selected == "🏠 Dashboard":
        st.session_state.current_page = "dashboard"
    elif selected == "📊 My Scrapes":
        st.session_state.current_page = "my_scrapes"
    elif selected == "⚙️ Settings":
        st.session_state.current_page = "settings"
    elif selected == "👥 All Users":
        st.session_state.current_page = "admin_users"
    elif selected == "📈 All Scrapes":
        st.session_state.current_page = "admin_scrapes"
    
    # Logout button
    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        logout_user()
        st.session_state.show_page = "landing"
        st.rerun()
    
    # User info
    st.sidebar.markdown("""
    <div class="sidebar-info">
        <small>
        🔧 <b>Your Account:</b><br>
        Email: {}<br>
        Role: {}<br>
        </small>
    </div>
    """.format(
        st.session_state.user['email'],
        "Admin" if st.session_state.user.get('is_admin') else "User"
    ), unsafe_allow_html=True)

def main():
    """Main application logic"""
    
    # Initialize page state
    if 'show_page' not in st.session_state:
        st.session_state.show_page = "landing"
    
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "dashboard"
    
    # Check authentication
    is_authenticated = check_authentication()
    
    if is_authenticated:
        # Show navigation for authenticated users
        show_navigation()
        
        # Route to appropriate page
        if st.session_state.current_page == "dashboard":
            from pages.Dashboard import show_dashboard
            show_dashboard()
        elif st.session_state.current_page == "my_scrapes":
            from pages.Dashboard import show_my_scrapes
            show_my_scrapes()
        elif st.session_state.current_page == "settings":
            from pages.Dashboard import show_settings
            show_settings()
        elif st.session_state.current_page == "admin_users" and st.session_state.user.get('is_admin'):
            from pages.Dashboard import show_admin_users
            show_admin_users()
        elif st.session_state.current_page == "admin_scrapes" and st.session_state.user.get('is_admin'):
            from pages.Dashboard import show_admin_scrapes
            show_admin_scrapes()
    
    else:
        # Handle non-authenticated pages
        if st.session_state.show_page == "login":
            from pages.Login import show_login_page
            show_login_page()
        elif st.session_state.show_page == "signup":
            from pages.Signup import show_signup_page
            show_signup_page()
        else:
            # Show landing page
            show_landing_page()

if __name__ == "__main__":
    main()