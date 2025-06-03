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


def safe_json_parse(response):
    """Safely parse JSON response with fallback error handling"""
    try:
        return response.json()
    except ValueError as e:
        # Response is not valid JSON - likely HTML error page
        st.error(f"🔧 Backend returned invalid response format. Status: {response.status_code}")
        st.error(f"Response preview: {response.text[:200]}...")
        return {
            "success": False,
            "message": f"Invalid JSON response from backend (Status: {response.status_code})",
            "results": [],
            "website": "error"
        }


def scrape_data(prompt: str) -> Tuple[List[Dict], str]:
    """
    Scrape data by calling the FastAPI backend instead of using Playwright directly.
    This solves the browser binary issues in Streamlit Cloud.
    
    Args:
        prompt: Natural language scraping request
        
    Returns:
        Tuple of (results_list, website_name)
    """
    
    # Input validation
    if not prompt or not prompt.strip():
        st.error("❌ Please enter a valid scraping request.")
        return [], 'invalid_input'
    
    if len(prompt.strip()) < 5:
        st.error("❌ Scraping request is too short. Please be more specific.")
        return [], 'invalid_input'
    
    # Check authentication
    if 'user' not in st.session_state or not st.session_state.user:
        st.error("❌ Authentication required for scraping.")
        return [], 'auth_error'
    
    username = st.session_state.user.get('username', '')
    is_admin = st.session_state.user.get('is_admin', False)
    
    if not username:
        st.error("❌ Invalid user session.")
        return [], 'auth_error'
    
    # Check scrape limit BEFORE attempting to scrape
    if not check_and_update_scrape_limit(username, is_admin):
        st.error("🚫 Daily scrape limit (5) exceeded. Try again tomorrow or contact admin for upgrade.")
        return [], 'limit_exceeded'
    
    # Check if backend is healthy
    if not check_backend_health():
        st.error("🔌 Scraping service is currently unavailable. Please try again later.")
        st.info("💡 Tip: If you're running locally, make sure your FastAPI server is running on port 8000")
        return [], 'service_unavailable'
    
    try:
        # Prepare request payload - match exactly what tester.py sends
        payload = {
            "prompt": prompt.strip(),
            "max_items": 50  # Default max items
        }
        
        # Debug log
        st.info(f"🔄 Sending request to: {BACKEND_URL}/scrape")
        
        # Make request to FastAPI backend
        response = requests.post(
            f"{BACKEND_URL}/scrape",
            json=payload,
            timeout=120,  # 2 minutes timeout for scraping
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
        )
        
        # Debug response
        st.info(f"📡 Response status: {response.status_code}")
        
        # Parse response safely
        if response.status_code == 200:
            data = safe_json_parse(response)
            
            # Handle the response format from your FastAPI
            if data.get("success", False):
                results = data.get("results", [])
                website = data.get("website", "unknown")
                message = data.get("message", "Scraping completed successfully!")
                
                # Validate results structure
                if not isinstance(results, list):
                    st.error("❌ Backend returned invalid results format")
                    return [], 'format_error'
                
                # Filter out any error entries
                valid_results = []
                for result in results:
                    if isinstance(result, dict) and 'error' not in result:
                        valid_results.append(result)
                
                if valid_results:
                    st.success(f"✅ {message}")
                    st.info(f"📊 Found {len(valid_results)} records from {website}")
                    return valid_results, website
                else:
                    st.warning("⚠️ No valid results found in response")
                    return [], website
            
            else:
                # Backend returned error in success=False format
                error_msg = data.get("message", "Unknown error occurred")
                st.error(f"❌ Scraping failed: {error_msg}")
                return [], 'backend_error'
        
        elif response.status_code == 400:
            # Bad request - try to parse error details
            try:
                error_data = safe_json_parse(response)
                error_detail = error_data.get("detail", "Invalid request")
            except:
                error_detail = "Invalid request format"
            
            st.error(f"❌ Invalid request: {error_detail}")
            return [], 'bad_request'
        
        elif response.status_code == 422:
            # Validation error
            try:
                error_data = safe_json_parse(response)
                error_detail = error_data.get("detail", "Validation error")
                if isinstance(error_detail, list) and len(error_detail) > 0:
                    error_detail = error_detail[0].get("msg", "Validation error")
            except:
                error_detail = "Request validation failed"
            
            st.error(f"❌ Validation error: {error_detail}")
            return [], 'validation_error'
        
        elif response.status_code == 500:
            # Internal server error
            try:
                error_data = safe_json_parse(response)
                error_detail = error_data.get("detail", "Internal server error")
            except:
                error_detail = "Internal server error"
            
            st.error(f"❌ Server error: {error_detail}")
            st.info("💡 This might be a temporary issue. Please try again in a moment.")
            return [], 'server_error'
        
        else:
            # Other HTTP errors
            st.error(f"❌ Request failed with status code: {response.status_code}")
            st.error(f"Response: {response.text[:200]}")
            return [], 'http_error'
    
    except requests.Timeout:
        st.error("⏱️ Request timed out. The website might be taking too long to respond.")
        st.info("💡 Try again with a simpler request or fewer items.")
        return [], 'timeout'
    
    except requests.ConnectionError:
        st.error("🔌 Could not connect to scraping service.")
        st.info("💡 Please check:")
        st.info("   • Your internet connection")
        st.info("   • That the backend server is running")
        st.info(f"   • Backend URL is correct: {BACKEND_URL}")
        return [], 'connection_error'
    
    except requests.RequestException as e:
        st.error(f"❌ Request failed: {str(e)}")
        return [], 'request_error'
    
    except Exception as e:
        st.error(f"❌ Unexpected error: {str(e)}")
        st.info("💡 Please try again or contact support if the issue persists.")
        return [], 'unexpected_error'


def get_scraping_status_message(status_code: str) -> str:
    """
    Get user-friendly message for scraping status codes
    """
    status_messages = {
        'invalid_input': 'Invalid or empty scraping request',
        'auth_error': 'Authentication or session error',
        'limit_exceeded': 'Daily scraping limit exceeded',
        'service_unavailable': 'Scraping service unavailable',
        'backend_error': 'Backend processing error',
        'bad_request': 'Invalid scraping request',
        'validation_error': 'Request validation failed',
        'server_error': 'Internal server error',
        'http_error': 'HTTP communication error',
        'timeout': 'Request timeout',
        'connection_error': 'Connection error',
        'request_error': 'Request processing error',
        'unexpected_error': 'Unexpected error occurred',
        'format_error': 'Invalid response format'
    }
    
    return status_messages.get(status_code, 'Unknown error')


def validate_scraping_prompt(prompt: str) -> Tuple[bool, str]:
    """
    Validate if the scraping prompt is reasonable
    Returns (is_valid, error_message)
    """
    if not prompt or not prompt.strip():
        return False, "Prompt cannot be empty"
    
    # Check minimum length
    if len(prompt.strip()) < 10:
        return False, "Prompt is too short. Please provide more details."
    
    # Check maximum length
    if len(prompt.strip()) > 500:
        return False, "Prompt is too long. Please keep it under 500 characters."
    
    # Check for potentially harmful requests
    harmful_keywords = [
        'hack', 'attack', 'exploit', 'password', 'credential',
        'private', 'personal', 'confidential', 'bank', 'payment',
        'login', 'admin', 'root', 'database'
    ]
    
    prompt_lower = prompt.lower()
    for keyword in harmful_keywords:
        if keyword in prompt_lower:
            return False, f"Request contains potentially harmful keyword: '{keyword}'"
    
    return True, ""


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


def get_example_prompts() -> List[str]:
    """Get list of example prompts for users"""
    return [
        "Get 20 mobile phones from Flipkart with price and rating",
        "Scrape 15 laptops from Amazon with specifications",
        "Find 10 headphones from Flipkart with discount information",
        "Get government notifications from ministry portal",
        "Extract 25 electronic products with price comparison"
    ]