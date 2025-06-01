import streamlit as st
import re
from utils.auth_utils import AuthManager

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Validate password strength"""
    if len(password) < 6:
        return False, "Password must be at least 6 characters long"
    
    if not re.search(r'[A-Za-z]', password):
        return False, "Password must contain at least one letter"
    
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    
    return True, "Password is valid"

def show_signup_page():
    """Display signup page"""
    
    st.markdown("""
    <div style="text-align: center; padding: 2rem 0;">
        <h1>📝 Create Your Account</h1>
        <p>Join the AI Web Scraper platform and start extracting data effortlessly</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Create centered signup form
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.container():
            st.markdown("""
            <div style="background: white; padding: 2rem; border-radius: 15px; 
                        box-shadow: 0 4px 20px rgba(0,0,0,0.1); margin: 2rem 0;">
            """, unsafe_allow_html=True)
            
            # Signup form
            with st.form("signup_form", clear_on_submit=False):
                st.markdown("### Create Your Account")
                
                username = st.text_input(
                    "Username",
                    placeholder="Choose a unique username",
                    help="This will be your login identifier"
                )
                
                email = st.text_input(
                    "Email Address",
                    placeholder="Enter your email address",
                    help="We'll use this for important notifications"
                )
                
                password = st.text_input(
                    "Password",
                    type="password",
                    placeholder="Create a strong password",
                    help="At least 6 characters with letters and numbers"
                )
                
                confirm_password = st.text_input(
                    "Confirm Password",
                    type="password",
                    placeholder="Re-enter your password"
                )
                
                # Terms and conditions
                terms_accepted = st.checkbox(
                    "I agree to the Terms of Service and Privacy Policy",
                    help="Required to create an account"
                )
                
                # Submit button
                submitted = st.form_submit_button(
                    "🚀 Create Account",
                    use_container_width=True,
                    type="primary"
                )
                
                if submitted:
                    # Validation checks
                    errors = []
                    
                    if not username or len(username.strip()) < 3:
                        errors.append("Username must be at least 3 characters long")
                    
                    if not email or not validate_email(email):
                        errors.append("Please enter a valid email address")
                    
                    if not password:
                        errors.append("Password is required")
                    else:
                        is_valid, password_msg = validate_password(password)
                        if not is_valid:
                            errors.append(password_msg)
                    
                    if password != confirm_password:
                        errors.append("Passwords do not match")
                    
                    if not terms_accepted:
                        errors.append("You must accept the Terms of Service")
                    
                    # Display errors or create account
                    if errors:
                        for error in errors:
                            st.error(error)
                    else:
                        # Create user account
                        auth_manager = AuthManager()
                        
                        with st.spinner("Creating your account..."):
                            result = auth_manager.create_user(
                                username.strip(),
                                email.strip().lower(),
                                password
                            )
                        
                        if result["success"]:
                            st.success("Account created successfully! Please login to continue.")
                            st.balloons()
                            
                            # Auto-redirect to login after a short delay
                            if st.button("Continue to Login →"):
                                st.session_state.show_page = "login"
                                st.rerun()
                        else:
                            st.error(result["message"])
            
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Additional options
            st.markdown("---")
            
            col_a, col_b = st.columns(2)
            
            with col_a:
                if st.button("🔐 Already have an account? Login", use_container_width=True):
                    st.session_state.show_page = "login"
                    st.rerun()
            
            with col_b:
                if st.button("🏠 Back to Home", use_container_width=True):
                    st.session_state.show_page = "landing"
                    st.rerun()
    
    # Benefits section
    st.markdown("---")
    st.markdown("### 🎯 What You Get With Your Account")
    
    benefits_col1, benefits_col2 = st.columns(2)
    
    with benefits_col1:
        st.markdown("""
        **🚀 Core Features:**
        - Unlimited web scraping
        - AI-powered prompt parsing
        - Stealth mode scraping
        - Multiple export formats
        """)
    
    with benefits_col2:
        st.markdown("""
        **📊 Data Management:**
        - Scrape history tracking
        - Data visualization charts
        - CSV & Excel downloads
        - Personal dashboard
        """)
    
    # Security notice
    st.info("""
    🔒 **Your Privacy & Security:**
    - All passwords are encrypted using industry-standard bcrypt
    - Your data is stored securely in MongoDB
    - We never share your personal information
    - You can delete your account anytime
    """)