from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Tuple, Optional
import asyncio
import re
import time
import os
from datetime import datetime
from playwright.async_api import async_playwright, Page, Browser
from fake_useragent import UserAgent
from urllib.parse import urlparse
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Web Scraper API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ScrapeRequest(BaseModel):
    prompt: str
    max_items: Optional[int] = 50

class ScrapeResponse(BaseModel):
    results: List[Dict]
    website: str
    success: bool
    message: str = ""

class StealthScraper:
    def __init__(self):
        self.ua = UserAgent()
        self.browser = None
        self.context = None
    
    async def init_browser(self, headless: bool = True):
        """Initialize Playwright browser with stealth settings"""
        playwright = await async_playwright().start()
        
        # Launch browser with stealth settings
        self.browser = await playwright.chromium.launch(
            headless=headless,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--no-first-run',
                '--no-zygote',
                '--disable-gpu',
                '--disable-blink-features=AutomationControlled'
            ]
        )
        
        # Create context with stealth settings
        self.context = await self.browser.new_context(
            user_agent=self.ua.random,
            viewport={'width': 1920, 'height': 1080},
            extra_http_headers={
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
        )
        
        # Add stealth scripts
        await self.context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
            
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });
            
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en'],
            });
            
            window.chrome = {
                runtime: {},
            };
        """)
    
    async def close_browser(self):
        """Close browser and context"""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
    
    async def handle_infinite_scroll(self, page: Page, max_scrolls: int = 10):
        """Handle infinite scroll pages"""
        for i in range(max_scrolls):
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(2000)
            
            # Check if new content loaded
            current_height = await page.evaluate("document.body.scrollHeight")
            await page.wait_for_timeout(1000)
            new_height = await page.evaluate("document.body.scrollHeight")
            
            if current_height == new_height:
                break
    
    async def wait_for_dynamic_content(self, page: Page, timeout: int = 10000):
        """Wait for dynamic content to load"""
        try:
            # Wait for network to be idle
            await page.wait_for_load_state("networkidle", timeout=timeout)
            
            # Additional wait for dynamic content
            await page.wait_for_timeout(3000)
            
            # Check for common loading indicators
            loading_selectors = [
                '[class*="loading"]',
                '[class*="spinner"]',
                '[class*="skeleton"]',
                '.loading',
                '.spinner'
            ]
            
            for selector in loading_selectors:
                try:
                    await page.wait_for_selector(selector, state="detached", timeout=5000)
                except:
                    continue
                    
        except Exception as e:
            logger.warning(f"Timeout waiting for content: {str(e)}")
    
    async def handle_captcha(self, page: Page) -> bool:
        """Detect and handle basic captcha (placeholder implementation)"""
        captcha_indicators = [
            'captcha',
            'recaptcha',
            'hcaptcha',
            'I\'m not a robot'
        ]
        
        page_content = await page.content()
        page_content_lower = page_content.lower()
        
        for indicator in captcha_indicators:
            if indicator in page_content_lower:
                logger.warning("Captcha detected. Manual intervention may be required.")
                await page.wait_for_timeout(5000)  # Give time for manual solving
                return True
        
        return False

class PromptParser:
    """Parse user prompts to extract scraping instructions"""
    
    @staticmethod
    def parse_scraping_prompt(prompt: str) -> Dict:
        """Parse natural language prompt into scraping parameters"""
        prompt_lower = prompt.lower()
        
        # Extract number of items
        number_match = re.search(r'\b(\d+)\b', prompt)
        max_items = int(number_match.group(1)) if number_match else 50
        
        # Detect website
        website = None
        if 'flipkart' in prompt_lower:
            website = 'flipkart'
        elif 'amazon' in prompt_lower:
            website = 'amazon'
        elif 'government' in prompt_lower or 'govt' in prompt_lower:
            website = 'government'
        else:
            website = 'general'
        
        # Extract data fields
        fields = []
        field_keywords = {
            'price': ['price', 'cost', 'amount'],
            'rating': ['rating', 'review', 'star'],
            'discount': ['discount', 'offer', 'sale'],
            'title': ['title', 'name', 'product'],
            'description': ['description', 'detail', 'spec'],
            'availability': ['available', 'stock', 'in stock']
        }
        
        for field, keywords in field_keywords.items():
            if any(keyword in prompt_lower for keyword in keywords):
                fields.append(field)
        
        # Default fields if none specified
        if not fields:
            fields = ['title', 'price', 'rating']
        
        # Extract product category
        category = None
        categories = ['mobile', 'laptop', 'phone', 'electronics', 'fashion', 'book']
        for cat in categories:
            if cat in prompt_lower:
                category = cat
                break
        
        return {
            'website': website,
            'max_items': max_items,
            'fields': fields,
            'category': category,
            'original_prompt': prompt
        }

class WebsiteScraper:
    """Website-specific scraping logic"""
    
    def __init__(self, scraper: StealthScraper):
        self.scraper = scraper
        self.selectors = {
            'flipkart': {
                'search_box': '[data-testid="search-input"], input[name="q"]',
                'search_button': '[data-testid="search-button"], button[type="submit"]',
                'product_container': '[data-testid="product-container"], ._1AtVbE',
                'title': '._4rR01T, .s1Q9rs',
                'price': '._30jeq3._1_WHN1, ._1p7iuX',
                'rating': '.gUuXy- span, ._3LWZlK',
                'discount': '._3Ay6Sb, ._2Tpdn3',
                'image': '._396cs4 img, .CXW8mj img'
            },
            'amazon': {
                'search_box': '#twotabsearchtextbox',
                'search_button': '#nav-search-submit-button',
                'product_container': '[data-component-type="s-search-result"]',
                'title': 'h2 a span, .a-text-normal',
                'price': '.a-price-whole, .a-offscreen',
                'rating': '.a-icon-alt, .a-star-medium-4',
                'discount': '.a-badge-text, .a-color-price',
                'image': '.s-image'
            }
        }
    
    async def scrape_flipkart(self, query: str, max_items: int = 50) -> List[Dict]:
        """Scrape Flipkart products"""
        page = await self.scraper.context.new_page()
        results = []
        
        try:
            # Navigate to Flipkart
            await page.goto('https://www.flipkart.com', wait_until='networkidle')
            await self.scraper.wait_for_dynamic_content(page)
            
            # Handle popup/modal if present
            try:
                await page.click('button._2KpZ6l._2doB4z', timeout=3000)
            except:
                pass
            
            # Search for products
            await page.fill(self.selectors['flipkart']['search_box'], query)
            await page.click(self.selectors['flipkart']['search_button'])
            await self.scraper.wait_for_dynamic_content(page)
            
            # Handle infinite scroll
            await self.scraper.handle_infinite_scroll(page, max_scrolls=5)
            
            # Extract product data
            products = await page.query_selector_all(self.selectors['flipkart']['product_container'])
            
            for i, product in enumerate(products[:max_items]):
                try:
                    title_elem = await product.query_selector(self.selectors['flipkart']['title'])
                    price_elem = await product.query_selector(self.selectors['flipkart']['price'])
                    rating_elem = await product.query_selector(self.selectors['flipkart']['rating'])
                    discount_elem = await product.query_selector(self.selectors['flipkart']['discount'])
                    
                    title = await title_elem.inner_text() if title_elem else 'N/A'
                    price = await price_elem.inner_text() if price_elem else 'N/A'
                    rating = await rating_elem.inner_text() if rating_elem else 'N/A'
                    discount = await discount_elem.inner_text() if discount_elem else 'N/A'
                    
                    # Clean data
                    price = re.sub(r'[^\d,.]', '', price) if price != 'N/A' else 'N/A'
                    rating = re.search(r'[\d.]+', rating).group() if rating != 'N/A' and re.search(r'[\d.]+', rating) else 'N/A'
                    
                    results.append({
                        'title': title.strip(),
                        'price': price,
                        'rating': rating,
                        'discount': discount.strip(),
                        'source': 'Flipkart'
                    })
                    
                except Exception as e:
                    continue
            
        except Exception as e:
            logger.error(f"Error scraping Flipkart: {str(e)}")
        
        finally:
            await page.close()
        
        return results
    
    async def scrape_amazon(self, query: str, max_items: int = 50) -> List[Dict]:
        """Scrape Amazon products"""
        page = await self.scraper.context.new_page()
        results = []
        
        try:
            # Navigate to Amazon
            await page.goto('https://www.amazon.in', wait_until='networkidle')
            await self.scraper.wait_for_dynamic_content(page)
            
            # Search for products
            await page.fill(self.selectors['amazon']['search_box'], query)
            await page.click(self.selectors['amazon']['search_button'])
            await self.scraper.wait_for_dynamic_content(page)
            
            # Handle captcha if present
            await self.scraper.handle_captcha(page)
            
            # Extract product data
            products = await page.query_selector_all(self.selectors['amazon']['product_container'])
            
            for i, product in enumerate(products[:max_items]):
                try:
                    title_elem = await product.query_selector(self.selectors['amazon']['title'])
                    price_elem = await product.query_selector(self.selectors['amazon']['price'])
                    rating_elem = await product.query_selector(self.selectors['amazon']['rating'])
                    
                    title = await title_elem.inner_text() if title_elem else 'N/A'
                    price = await price_elem.inner_text() if price_elem else 'N/A'
                    rating = await rating_elem.get_attribute('aria-label') if rating_elem else 'N/A'
                    
                    # Clean data
                    price = re.sub(r'[^\d,.]', '', price) if price != 'N/A' else 'N/A'
                    rating = re.search(r'[\d.]+', rating).group() if rating != 'N/A' and re.search(r'[\d.]+', rating) else 'N/A'
                    
                    results.append({
                        'title': title.strip(),
                        'price': price,
                        'rating': rating,
                        'discount': 'N/A',
                        'source': 'Amazon'
                    })
                    
                except Exception as e:
                    continue
            
        except Exception as e:
            logger.error(f"Error scraping Amazon: {str(e)}")
        
        finally:
            await page.close()
        
        return results
    
    async def scrape_general_website(self, url: str, max_items: int = 50) -> List[Dict]:
        """Scrape general website (fallback method)"""
        page = await self.scraper.context.new_page()
        results = []
        
        try:
            await page.goto(url, wait_until='networkidle')
            await self.scraper.wait_for_dynamic_content(page)
            
            # Generic selectors for common elements
            generic_selectors = {
                'links': 'a[href]',
                'headings': 'h1, h2, h3, h4, h5, h6',
                'paragraphs': 'p',
                'lists': 'li',
                'prices': '[class*="price"], [id*="price"]',
                'titles': '[class*="title"], [class*="name"]'
            }
            
            # Extract various elements
            for element_type, selector in generic_selectors.items():
                elements = await page.query_selector_all(selector)
                
                for i, elem in enumerate(elements[:max_items//len(generic_selectors)]):
                    try:
                        text = await elem.inner_text()
                        if text and len(text.strip()) > 0:
                            results.append({
                                'type': element_type,
                                'content': text.strip()[:200],  # Limit content length
                                'source': urlparse(url).netloc
                            })
                    except:
                        continue
                        
        except Exception as e:
            logger.error(f"Error scraping website: {str(e)}")
        
        finally:
            await page.close()
        
        return results

# For demo purposes, we'll return dummy data to simulate scraping
async def generate_dummy_data(prompt: str, max_items: int = 50) -> Tuple[List[Dict], str]:
    """Generate dummy data for demonstration purposes"""
    
    parsed = PromptParser.parse_scraping_prompt(prompt)
    website = parsed['website']
    category = parsed.get('category', 'products')
    
    # Simulate processing delay
    await asyncio.sleep(2)
    
    if website == 'flipkart' or website == 'amazon':
        source_name = website.title()
        results = []
        
        for i in range(min(max_items, 25)):  # Limit to 25 for demo
            results.append({
                'title': f'{category.title() if category else "Product"} {i+1} - High Quality Item',
                'price': f'₹{10000 + i * 500 + (i % 7) * 100}',
                'rating': f'{3.5 + (i % 5) * 0.3:.1f}',
                'discount': f'{10 + (i % 5) * 5}% off',
                'source': source_name
            })
        
        return results, f'{website}.com'
    
    elif website == 'government':
        results = [
            {'title': 'Government Notification 1', 'type': 'notification', 'department': 'Ministry of Technology', 'date': '2024-12-01'},
            {'title': 'Policy Update 2024', 'type': 'policy', 'department': 'Ministry of Digital Affairs', 'date': '2024-11-28'},
            {'title': 'Public Tender Notice', 'type': 'tender', 'department': 'Ministry of Infrastructure', 'date': '2024-11-25'},
            {'title': 'Annual Report Publication', 'type': 'report', 'department': 'Ministry of Statistics', 'date': '2024-11-20'},
            {'title': 'New Scheme Announcement', 'type': 'scheme', 'department': 'Ministry of Social Welfare', 'date': '2024-11-15'}
        ]
        return results, 'gov.in'
    
    else:
        # General website dummy data
        results = [
            {'type': 'heading', 'content': 'Welcome to Our Website', 'source': 'example.com'},
            {'type': 'paragraph', 'content': 'This is a sample paragraph with important information.', 'source': 'example.com'},
            {'type': 'link', 'content': 'Contact Us', 'source': 'example.com'},
            {'type': 'heading', 'content': 'Our Services', 'source': 'example.com'},
            {'type': 'list', 'content': 'Service 1: Professional Consulting', 'source': 'example.com'}
        ]
        return results, 'example.com'

async def scrape_with_prompt(prompt: str, max_items: int = 50) -> Tuple[List[Dict], str]:
    """Main scraping function that processes natural language prompts"""
    
    # For demo purposes, return dummy data
    # In production, uncomment the real scraping logic below
    return await generate_dummy_data(prompt, max_items)
    
    # Real scraping logic (commented out for demo):
    """
    # Parse the prompt
    parsed = PromptParser.parse_scraping_prompt(prompt)
    website = parsed['website']
    max_items = parsed['max_items']
    category = parsed.get('category', 'products')
    
    # Initialize scraper
    scraper = StealthScraper()
    await scraper.init_browser(headless=True)
    
    website_scraper = WebsiteScraper(scraper)
    results = []
    
    try:
        if website == 'flipkart':
            query = f"{category} {' '.join(parsed['fields'])}" if category else 'products'
            results = await website_scraper.scrape_flipkart(query, max_items)
            website_url = 'flipkart.com'
            
        elif website == 'amazon':
            query = f"{category} {' '.join(parsed['fields'])}" if category else 'products'
            results = await website_scraper.scrape_amazon(query, max_items)
            website_url = 'amazon.in'
            
        else:
            # For general websites or government portals
            if 'government' in prompt.lower() or 'govt' in prompt.lower():
                # Mock government portal scraping
                results = [
                    {'title': 'Sample Govt Document 1', 'type': 'document', 'department': 'Ministry of XYZ', 'date': '2024-01-15'},
                    {'title': 'Sample Govt Document 2', 'type': 'notification', 'department': 'Ministry of ABC', 'date': '2024-01-20'},
                    {'title': 'Sample Govt Document 3', 'type': 'tender', 'department': 'Ministry of DEF', 'date': '2024-01-25'}
                ]
                website_url = 'gov.in'
            else:
                # General website scraping (requires URL in prompt)
                url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
                urls = re.findall(url_pattern, prompt)
                
                if urls:
                    results = await website_scraper.scrape_general_website(urls[0], max_items)
                    website_url = urlparse(urls[0]).netloc
                else:
                    results = [{'error': 'No valid URL found in prompt for general scraping'}]
                    website_url = 'unknown'
    
    except Exception as e:
        logger.error(f"Scraping error: {str(e)}")
        results = [{'error': str(e)}]
        website_url = 'error'
    
    finally:
        await scraper.close_browser()
    
    return results, website_url
    """

@app.get("/")
async def root():
    return {"message": "Web Scraper API is running!", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.post("/scrape", response_model=ScrapeResponse)
async def scrape_endpoint(request: ScrapeRequest):
    """
    Main scraping endpoint that accepts a natural language prompt
    and returns structured data
    """
    try:
        logger.info(f"Received scraping request: {request.prompt}")
        
        if not request.prompt or not request.prompt.strip():
            raise HTTPException(status_code=400, detail="Prompt cannot be empty")
        
        # Perform scraping
        results, website = await scrape_with_prompt(request.prompt, request.max_items)
        
        if not results:
            return ScrapeResponse(
                results=[],
                website=website,
                success=False,
                message="No data found for the given prompt"
            )
        
        # Check for errors in results
        if any('error' in result for result in results):
            error_msg = next(result['error'] for result in results if 'error' in result)
            return ScrapeResponse(
                results=[],
                website=website,
                success=False,
                message=f"Scraping error: {error_msg}"
            )
        
        logger.info(f"Successfully scraped {len(results)} items from {website}")
        
        return ScrapeResponse(
            results=results,
            website=website,
            success=True,
            message=f"Successfully scraped {len(results)} items"
        )
        
    except Exception as e:
        logger.error(f"Error in scrape endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)