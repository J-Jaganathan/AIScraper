import streamlit as st
from utils.auth_utils import AuthManager, login_user

def show_login_page():
    """Display login page"""
    
    st.markdown("""
    <div style="text-align: center; padding: 2rem 0;">
        <h1>🔐 Login to AI Web Scraper</h1>
        <p>Enter your credentials to access the scraping platform</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Create centered login form
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.container():
            st.markdown("""
            <div style="background: white; padding: 2rem; border-radius: 15px; 
                        box-shadow: 0 4px 20px rgba(0,0,0,0.1); margin: 2rem 0;">
            """, unsafe_allow_html=True)
            
            # Login form
            with st.form("login_form", clear_on_submit=False):
                st.markdown("### Enter Your Details")
                
                username = st.text_input(
                    "Username",
                    placeholder="Enter your username",
                    help="Use the username you created during signup"
                )
                
                password = st.text_input(
                    "Password",
                    type="password",
                    placeholder="Enter your password",
                    help="Your password is encrypted and secure"
                )
                
                # Submit button
                submitted = st.form_submit_button(
                    "🚀 Login",
                    use_container_width=True,
                    type="primary"
                )
                
                if submitted:
                    if not username or not password:
                        st.error("Please fill in all fields")
                    else:
                        # Authenticate user
                        auth_manager = AuthManager()
                        
                        with st.spinner("Authenticating..."):
                            result = auth_manager.authenticate_user(username, password)
                        
                        if result["success"]:
                            st.success("Login successful! Redirecting...")
                            login_user(result)
                            st.session_state.show_page = "dashboard"
                            st.rerun()
                        else:
                            st.error(result["message"])
            
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Additional options
            st.markdown("---")
            
            col_a, col_b = st.columns(2)
            
            with col_a:
                if st.button("📝 Don't have an account? Sign Up", use_container_width=True):
                    st.session_state.show_page = "signup"
                    st.rerun()
            
            with col_b:
                if st.button("🏠 Back to Home", use_container_width=True):
                    st.session_state.show_page = "landing"
                    st.rerun()
    
    # Demo credentials info
    st.markdown("---")
    st.info("""
    **Demo Credentials:**
    - Username: `demo_user` | Password: `demo123`
    - Admin Username: `admin` | Password: `admin123`
    
    *Note: These are created automatically if they don't exist*
    """)
    
    # Quick setup for demo
    if st.button("🚀 Quick Demo Setup", help="Creates demo accounts automatically"):
        auth_manager = AuthManager()
        
        # Create demo user
        demo_result = auth_manager.create_user("demo_user", "demo@example.com", "demo123")
        admin_result = auth_manager.create_user("admin", "admin@example.com", "admin123", is_admin=True)
        
        if demo_result["success"] or "already exists" in demo_result["message"]:
            st.success("Demo accounts ready! Use credentials above to login.")
        else:
            st.error("Error setting up demo accounts")