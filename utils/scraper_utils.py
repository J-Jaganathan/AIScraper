import json
import os
import requests
import streamlit as st
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple
from urllib.parse import urlparse


# Configuration - Update this with your actual FastAPI backend URL
BACKEND_URL = os.getenv("SCRAPER_BACKEND_URL", "http://localhost:8000")


def check_and_update_scrape_limit(username: str, is_admin: bool = False) -> bool:
    """
    Check if user has exceeded daily scrape limit and update count.
    Returns True if scraping is allowed, False if limit exceeded.
    """
    if is_admin:
        return True
    
    # Ensure data directory exists
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    log_file = data_dir / "scrape_log.json"
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Load existing log
    scrape_log = {}
    if log_file.exists():
        try:
            with open(log_file, 'r') as f:
                scrape_log = json.load(f)
        except (json.JSONDecodeError, IOError):
            scrape_log = {}
    
    # Initialize user data if not exists
    if username not in scrape_log:
        scrape_log[username] = {}
    
    # Get today's count
    today_count = scrape_log[username].get(today, 0)
    
    # Check limit
    if today_count >= 5:
        return False
    
    # Increment count
    scrape_log[username][today] = today_count + 1
    
    # Clean old entries (keep only last 30 days)
    current_date = datetime.now()
    for user in scrape_log:
        dates_to_remove = []
        for date_str in scrape_log[user]:
            try:
                log_date = datetime.strptime(date_str, "%Y-%m-%d")
                if (current_date - log_date).days > 30:
                    dates_to_remove.append(date_str)
            except ValueError:
                dates_to_remove.append(date_str)
        
        for date_str in dates_to_remove:
            del scrape_log[user][date_str]
    
    # Save updated log
    try:
        with open(log_file, 'w') as f:
            json.dump(scrape_log, f, indent=2)
    except IOError as e:
        st.warning(f"Could not save scrape log: {e}")
    
    return True


def check_backend_health() -> bool:
    """Check if the FastAPI backend is running and healthy"""
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        return response.status_code == 200
    except requests.RequestException:
        return False


def scrape_data(prompt: str) -> Tuple[List[Dict], str]:
    """
    Scrape data by calling the FastAPI backend instead of using Playwright directly.
    This solves the browser binary issues in Streamlit Cloud.
    
    Args:
        prompt: Natural language scraping request
        
    Returns:
        Tuple of (results_list, website_name)
    """
    
    # Check rate limiting BEFORE attempting to scrape
    if 'user' not in st.session_state or not st.session_state.user:
        st.error("❌ Authentication required for scraping.")
        return [], 'error'
    
    username = st.session_state.user.get('username', '')
    is_admin = st.session_state.user.get('is_admin', False)
    
    if not username:
        st.error("❌ Invalid user session.")
        return [], 'error'
    
    # Check scrape limit
    if not check_and_update_scrape_limit(username, is_admin):
        st.error("🚫 Daily scrape limit (5) exceeded. Try again tomorrow or contact admin for upgrade.")
        return [], 'limit_exceeded'
    
    # Check if backend is healthy
    if not check_backend_health():
        st.error("🔌 Scraping service is currently unavailable. Please try again later.")
        return [], 'service_unavailable'
    
    try:
        # Prepare request payload
        payload = {
            "prompt": prompt,
            "max_items": 50  # Default max items
        }
        
        # Make request to FastAPI backend
        response = requests.post(
            f"{BACKEND_URL}/scrape",
            json=payload,
            timeout=120,  # 2 minutes timeout for scraping
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("success", False):
                results = data.get("results", [])
                website = data.get("website", "unknown")
                
                # Log successful scrape
                st.success(f"✅ {data.get('message', 'Scraping completed successfully!')}")
                
                return results, website
            else:
                # Backend returned error
                error_msg = data.get("message", "Unknown error occurred")
                st.error(f"❌ Scraping failed: {error_msg}")
                return [], 'backend_error'
        
        elif response.status_code == 400:
            # Bad request
            error_detail = response.json().get("detail", "Invalid request")
            st.error(f"❌ Invalid request: {error_detail}")
            return [], 'bad_request'
        
        elif response.status_code == 500:
            # Internal server error
            error_detail = response.json().get("detail", "Internal server error")
            st.error(f"❌ Server error: {error_detail}")
            return [], 'server_error'
        
        else:
            # Other HTTP errors
            st.error(f"❌ Request failed with status code: {response.status_code}")
            return [], 'http_error'
    
    except requests.Timeout:
        st.error("⏱️ Request timed out. The website might be taking too long to respond.")
        return [], 'timeout'
    
    except requests.ConnectionError:
        st.error("🔌 Could not connect to scraping service. Please check your internet connection.")
        return [], 'connection_error'
    
    except requests.RequestException as e:
        st.error(f"❌ Request failed: {str(e)}")
        return [], 'request_error'
    
    except Exception as e:
        st.error(f"❌ Unexpected error: {str(e)}")
        return [], 'unexpected_error'


def get_scraping_status_message(status_code: str) -> str:
    """
    Get user-friendly message for scraping status codes
    """
    status_messages = {
        'error': 'Authentication or session error',
        'limit_exceeded': 'Daily scraping limit exceeded',
        'service_unavailable': 'Scraping service unavailable',
        'backend_error': 'Backend processing error',
        'bad_request': 'Invalid scraping request',
        'server_error': 'Internal server error',
        'http_error': 'HTTP communication error',
        'timeout': 'Request timeout',
        'connection_error': 'Connection error',
        'request_error': 'Request processing error',
        'unexpected_error': 'Unexpected error occurred'
    }
    
    return status_messages.get(status_code, 'Unknown error')


def validate_scraping_prompt(prompt: str) -> bool:
    """
    Validate if the scraping prompt is reasonable
    """
    if not prompt or not prompt.strip():
        return False
    
    # Check minimum length
    if len(prompt.strip()) < 10:
        return False
    
    # Check for potentially harmful requests
    harmful_keywords = [
        'hack', 'attack', 'exploit', 'password', 'credential',
        'private', 'personal', 'confidential', 'bank', 'payment'
    ]
    
    prompt_lower = prompt.lower()
    for keyword in harmful_keywords:
        if keyword in prompt_lower:
            return False
    
    return True


def estimate_scraping_time(prompt: str) -> int:
    """
    Estimate scraping time in seconds based on prompt
    """
    prompt_lower = prompt.lower()
    
    # Base time
    base_time = 10
    
    # Add time based on complexity
    if any(site in prompt_lower for site in ['flipkart', 'amazon']):
        base_time += 20
    
    # Add time based on number of items
    import re
    number_match = re.search(r'\b(\d+)\b', prompt)
    if number_match:
        num_items = int(number_match.group(1))
        base_time += min(num_items // 10, 30)  # Cap at 30 extra seconds
    
    return base_time