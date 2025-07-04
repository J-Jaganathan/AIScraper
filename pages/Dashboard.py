import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import io
import base64
from utils.auth_utils import AuthManager, require_auth, require_admin
from utils.scraper_utils import scrape_data
from utils.robots_utils import is_allowed_to_scrape
import plotly.express as px
import plotly.graph_objects as go
import re
from utils.ui_utils import hide_streamlit_sidebar, apply_custom_styling

# Hide sidebar immediately when page loads
hide_streamlit_sidebar()
apply_custom_styling()
# CSS for the logout button and header
st.markdown("""
<style>
    /* Top header bar with logout button */
    .header-bar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 1rem 2rem;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }
    
    .header-title {
        font-size: 1.5rem;
        font-weight: bold;
        margin: 0;
    }
    
    .logout-btn {
        background: rgba(255,255,255,0.2);
        border: 1px solid rgba(255,255,255,0.3);
        padding: 0.5rem 1rem;
        border-radius: 20px;
        color: white;
        text-decoration: none;
        transition: all 0.3s ease;
        cursor: pointer;
        font-weight: 500;
    }
    
    .logout-btn:hover {
        background: rgba(255,255,255,0.3);
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    
    /* Navigation pills */
    .nav-pills {
        display: flex;
        gap: 1rem;
        margin-bottom: 2rem;
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
    }
    
    .nav-pill {
        padding: 0.5rem 1rem;
        border-radius: 20px;
        border: none;
        background: white;
        color: #666;
        cursor: pointer;
        transition: all 0.3s ease;
        text-decoration: none;
    }
    
    .nav-pill.active {
        background: #667eea;
        color: white;
    }
    
    .nav-pill:hover {
        background: #667eea;
        color: white;
        transform: translateY(-2px);
    }
</style>
""", unsafe_allow_html=True)

def show_header_with_logout():
    """Show header bar with logout button"""
    
    # Create header with logout button
    header_html = f"""
    <div class="header-bar">
        <div>
            <h2 class="header-title">🕷️ AI Web Scraper Dashboard</h2>
            <p style="margin: 0; opacity: 0.9;">Welcome back, <strong>{st.session_state.user['username']}</strong>!</p>
        </div>
        <div>
            <span style="margin-right: 1rem; opacity: 0.8;">
                {st.session_state.user.get('email', '')}
            </span>
        </div>
    </div>
    """
    
    st.markdown(header_html, unsafe_allow_html=True)
    
    # Logout button in a separate container for better control
    col1, col2, col3 = st.columns([6, 1, 1])
    
    with col3:
        if st.button("🚪 Logout", key="logout_btn", help="Return to home page"):
            # Clear session state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            
            # Set page to landing
            st.session_state.show_page = "landing"
            st.rerun()

def show_navigation_pills():
    """Show navigation as horizontal pills"""
    
    # Navigation options
    nav_options = {
        'Dashboard': 'dashboard',
        'Scrape History': 'history'
    }
    
    # Add admin panel if user is admin
    if st.session_state.get('user', {}).get('is_admin', False):
        nav_options['Admin Panel'] = 'admin'
    
    # Create navigation pills
    cols = st.columns(len(nav_options))
    
    for i, (page_name, page_key) in enumerate(nav_options.items()):
        with cols[i]:
            if st.button(
                page_name, 
                key=f"nav_{page_key}",
                use_container_width=True,
                type="primary" if st.session_state.get('page', 'dashboard') == page_key else "secondary"
            ):
                st.session_state.page = page_key
                st.rerun()

def show_dashboard():
    """Main dashboard for authenticated users"""
    require_auth()
    
    # Quick stats
    auth_manager = AuthManager()
    user_scrapes = auth_manager.get_user_scrapes(st.session_state.user['id'])
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Scrapes", len(user_scrapes))
    
    with col2:
        recent_scrapes = [s for s in user_scrapes if s['created_at'] > datetime.utcnow() - timedelta(days=7)]
        st.metric("This Week", len(recent_scrapes))
    
    with col3:
        successful_scrapes = [s for s in user_scrapes if s['status'] == 'completed']
        success_rate = (len(successful_scrapes) / len(user_scrapes) * 100) if user_scrapes else 0
        st.metric("Success Rate", f"{success_rate:.1f}%")
    
    with col4:
        total_records = sum(s.get('record_count', 0) for s in user_scrapes)
        st.metric("Total Records", total_records)
    
    st.markdown("---")
    
    # Main scraping interface
    st.markdown("### 🤖 AI Scraping Assistant")
    st.markdown("Describe what you want to scrape in natural language:")
    
    # Example prompts
    with st.expander("💡 Example Prompts", expanded=False):
        examples = [
            "Scrape top 50 mobiles from Flipkart with price, rating, and discount",
            "Get 30 laptops from Amazon with specifications and reviews", 
            "Extract government notifications from ministry portal",
            "Scrape product data from e-commerce website https://example.com"
        ]
        
        for i, example in enumerate(examples, 1):
            if st.button(f"Use Example {i}", key=f"example_{i}"):
                st.session_state.scrape_prompt = example
    
    # Main prompt input
    prompt = st.text_area(
        "Your Scraping Request:",
        height=100,
        placeholder="e.g., 'Scrape top 50 mobiles from Flipkart with price, rating, discount'",
        value=st.session_state.get('scrape_prompt', ''),
        help="Describe what data you want to extract and from which website"
    )
    
    # Scraping button
    if st.button("🚀 Start Scraping", type="primary", use_container_width=True):
        if not prompt.strip():
            st.error("Please enter a scraping request")
        else:
            # Check robots.txt compliance for non-admin users
            user_agent = "MyScraperBot"
            urls = re.findall(r'https?://[^\s]+', prompt)
            target_url = urls[0] if urls else None
            is_admin = st.session_state.user.get("is_admin", False)
            
            if target_url and not is_admin:
                allowed = is_allowed_to_scrape(user_agent, target_url)
                if not allowed:
                    st.error("🚫 robots.txt disallows scraping this site for your role.")
                    st.stop()
            
            scraping_container = st.container()
            
            with scraping_container:
                st.info("🔄 Scraping in progress... This may take a few moments.")
                
                # Progress bar
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                try:
                    # Update progress
                    progress_bar.progress(25)
                    status_text.text("Initializing browser...")
                    
                    # Perform scraping
                    results, website = scrape_data(prompt)
                    
                    progress_bar.progress(75)
                    status_text.text("Processing results...")
                    
                    if results and not any('error' in result for result in results):
                        # Save to database
                        scrape_id = auth_manager.save_scrape_result(
                            st.session_state.user['id'],
                            prompt,
                            website,
                            results
                        )
                        
                        progress_bar.progress(100)
                        status_text.text("✅ Scraping completed successfully!")
                        
                        st.success(f"Successfully scraped {len(results)} records!")
                        
                        # Display results
                        display_scraping_results(results, prompt, website)
                        
                    else:
                        st.error("Scraping failed or returned no results")
                        if results:
                            st.write("Error details:", results)
                        
                except Exception as e:
                    st.error(f"Scraping failed: {str(e)}")
                    progress_bar.progress(0)
                    status_text.text("")

def display_scraping_results(results, prompt, website):
    """Display scraping results with visualizations and download options"""
    
    if not results:
        st.warning("No data to display")
        return
    
    st.markdown("---")
    st.markdown("### 📊 Scraping Results")
    
    # Convert to DataFrame
    df = pd.DataFrame(results)
    
    # Results summary
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown(f"**Query:** {prompt}")
        st.markdown(f"**Source:** {website}")
        st.markdown(f"**Records Found:** {len(results)}")
    
    with col2:
        st.markdown("**Export Options:**")
        
        # CSV download
        csv_data = df.to_csv(index=False)
        st.download_button(
            "📄 Download CSV",
            csv_data,
            file_name=f"scraped_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
        
        # Excel download
        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False, engine='openpyxl')
        excel_data = excel_buffer.getvalue()
        
        st.download_button(
            "📊 Download Excel",
            excel_data,
            file_name=f"scraped_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    
    # Data preview
    st.markdown("### 📋 Data Preview")
    st.dataframe(df, use_container_width=True, height=400)
    
    # Visualizations (rest of the function remains the same)
    if len(df) > 1 and any(col in df.columns for col in ['price', 'rating', 'discount']):
        st.markdown("### 📈 Data Visualization")
        
        viz_col1, viz_col2 = st.columns(2)
        
        # Price distribution
        if 'price' in df.columns:
            with viz_col1:
                try:
                    # Clean price data
                    price_data = df['price'].replace('N/A', None).dropna()
                    price_numeric = pd.to_numeric(price_data.str.replace(',', ''), errors='coerce').dropna()
                    
                    if len(price_numeric) > 0:
                        fig = px.histogram(x=price_numeric, title="Price Distribution", nbins=20)
                        fig.update_layout(xaxis_title="Price", yaxis_title="Count")
                        st.plotly_chart(fig, use_container_width=True)
                except:
                    st.info("Could not generate price chart")
        
        # Rating distribution
        if 'rating' in df.columns:
            with viz_col2:
                try:
                    # Clean rating data
                    rating_data = df['rating'].replace('N/A', None).dropna()
                    rating_numeric = pd.to_numeric(rating_data.str.replace(r'[^\d.]', '', regex=True), errors='coerce').dropna()
                    
                    if len(rating_numeric) > 0:
                        fig = px.histogram(x=rating_numeric, title="Rating Distribution", nbins=10)
                        fig.update_layout(xaxis_title="Rating", yaxis_title="Count")
                        st.plotly_chart(fig, use_container_width=True)
                except:
                    st.info("Could not generate rating chart")

def show_scrape_history():
    """Display user's scraping history"""
    require_auth()
    
    st.markdown("### 📚 Your Scraping History")
    
    auth_manager = AuthManager()
    user_scrapes = auth_manager.get_user_scrapes(st.session_state.user['id'])
    
    if not user_scrapes:
        st.info("No scraping history found. Start your first scrape!")
        return
    
    # Convert to DataFrame for better display
    history_data = []
    for scrape in user_scrapes:
        history_data.append({
            'Date': scrape['created_at'].strftime('%Y-%m-%d %H:%M'),
            'Query': scrape['prompt'][:50] + '...' if len(scrape['prompt']) > 50 else scrape['prompt'],
            'Website': scrape.get('website', 'N/A'),
            'Records': scrape.get('record_count', 0),
            'Status': scrape['status'].title(),
            'ID': str(scrape['_id'])
        })
    
    df_history = pd.DataFrame(history_data)
    st.dataframe(df_history, use_container_width=True)
    
    # Allow viewing individual scrape results
    st.markdown("### 🔍 View Scrape Details")
    scrape_ids = [str(s['_id']) for s in user_scrapes]
    selected_id = st.selectbox("Select a scrape to view details:", [''] + scrape_ids)
    
    if selected_id:
        selected_scrape = next(s for s in user_scrapes if str(s['_id']) == selected_id)
        
        st.markdown(f"**Query:** {selected_scrape['prompt']}")
        st.markdown(f"**Website:** {selected_scrape.get('website', 'N/A')}")
        st.markdown(f"**Date:** {selected_scrape['created_at']}")
        st.markdown(f"**Status:** {selected_scrape['status'].title()}")
        
        if selected_scrape.get('results') and selected_scrape['status'] == 'completed':
            results_df = pd.DataFrame(selected_scrape['results'])
            st.dataframe(results_df, use_container_width=True)
            
            # Download options
            col1, col2 = st.columns(2)
            with col1:
                csv_data = results_df.to_csv(index=False)
                st.download_button(
                    "📄 Download CSV",
                    csv_data,
                    file_name=f"scrape_{selected_id}_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
            
            with col2:
                excel_buffer = io.BytesIO()
                results_df.to_excel(excel_buffer, index=False, engine='openpyxl')
                excel_data = excel_buffer.getvalue()
                
                st.download_button(
                    "📊 Download Excel",
                    excel_data,
                    file_name=f"scrape_{selected_id}_{datetime.now().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

def show_admin_panel():
    """Admin panel to view all users and their scrapes"""
    require_admin()
    
    st.markdown("### 👑 Admin Panel")
    
    auth_manager = AuthManager()
    
    # Admin stats
    all_users = auth_manager.get_all_users_admin()
    all_scrapes = auth_manager.get_all_scrapes_admin()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Users", len(all_users))
    
    with col2:
        st.metric("Total Scrapes", len(all_scrapes))
    
    with col3:
        successful_scrapes = [s for s in all_scrapes if s['status'] == 'completed']
        success_rate = (len(successful_scrapes) / len(all_scrapes) * 100) if all_scrapes else 0
        st.metric("Global Success Rate", f"{success_rate:.1f}%")
    
    with col4:
        total_records = sum(s.get('record_count', 0) for s in all_scrapes)
        st.metric("Total Records", total_records)
    
    # Users table
    st.markdown("### 👥 All Users")
    users_data = []
    for user in all_users:
        user_scrapes = [s for s in all_scrapes if s.get('username') == user['username']]
        users_data.append({
            'Username': user['username'],
            'Email': user['email'],
            'Role': 'Admin' if user.get('is_admin') else 'User',
            'Scrapes': len(user_scrapes),
            'Joined': user['created_at'].strftime('%Y-%m-%d'),
            'Last Active': user.get('last_login', user['created_at']).strftime('%Y-%m-%d') if user.get('last_login') else user['created_at'].strftime('%Y-%m-%d')
        })
    
    users_df = pd.DataFrame(users_data)
    st.dataframe(users_df, use_container_width=True)
    
    # All scrapes table
    st.markdown("### 🕷️ All Scrapes")
    scrapes_data = []
    for scrape in all_scrapes[-100:]:  # Show last 100 scrapes
        scrapes_data.append({
            'Date': scrape['created_at'].strftime('%Y-%m-%d %H:%M'),
            'User': scrape.get('username', 'Unknown'),
            'Query': scrape['prompt'][:50] + '...' if len(scrape['prompt']) > 50 else scrape['prompt'],
            'Website': scrape.get('website', 'N/A'),
            'Records': scrape.get('record_count', 0),
            'Status': scrape['status'].title()
        })
    
    scrapes_df = pd.DataFrame(scrapes_data)
    st.dataframe(scrapes_df, use_container_width=True)
    
    # Usage analytics
    st.markdown("### 📈 Usage Analytics")
    
    if all_scrapes:
        # Scrapes over time
        scrapes_by_date = {}
        for scrape in all_scrapes:
            date_key = scrape['created_at'].strftime('%Y-%m-%d')
            scrapes_by_date[date_key] = scrapes_by_date.get(date_key, 0) + 1
        
        dates = sorted(scrapes_by_date.keys())
        counts = [scrapes_by_date[date] for date in dates]
        
        fig = px.line(x=dates, y=counts, title="Scrapes Over Time")
        fig.update_layout(xaxis_title="Date", yaxis_title="Number of Scrapes")
        st.plotly_chart(fig, use_container_width=True)
        
        # Top websites
        website_counts = {}
        for scrape in all_scrapes:
            website = scrape.get('website', 'Unknown')
            website_counts[website] = website_counts.get(website, 0) + 1
        
        if website_counts:
            top_websites = sorted(website_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            websites, counts = zip(*top_websites)
            
            fig = px.bar(x=list(websites), y=list(counts), title="Top 10 Scraped Websites")
            fig.update_layout(xaxis_title="Website", yaxis_title="Scrape Count")
            st.plotly_chart(fig, use_container_width=True)

# Main dashboard logic
def main():
    """Main function to handle dashboard navigation"""
    require_auth()
    
    # Show header with logout button
    show_header_with_logout()
    
    # Show navigation pills
    show_navigation_pills()
    
    # Initialize page state
    if 'page' not in st.session_state:
        st.session_state.page = 'dashboard'
    
    # Show selected page
    if st.session_state.page == 'dashboard':
        show_dashboard()
    elif st.session_state.page == 'history':
        show_scrape_history()
    elif st.session_state.page == 'admin':
        show_admin_panel()

if __name__ == "__main__":
    main()