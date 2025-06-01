
import urllib.robotparser
import urllib.robotparser
from urllib.parse import urlparse

def is_allowed_to_scrape(user_agent: str, target_url: str) -> bool:
    """
    Check if scraping is allowed according to robots.txt
    
    Args:
        user_agent: User agent string for the scraper
        target_url: URL to check for scraping permission
        
    Returns:
        bool: True if scraping is allowed, False otherwise
    """
    try:
        parsed_url = urlparse(target_url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        
        rp = urllib.robotparser.RobotFileParser()
        rp.set_url(f"{base_url}/robots.txt")
        rp.read()
        
        return rp.can_fetch(user_agent, target_url)
    except Exception as e:
        print(f"[robots_utils] Failed to read robots.txt: {e}")
        return False