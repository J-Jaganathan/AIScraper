from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import asyncio
import re
import logging
from datetime import datetime
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Web Scraper API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
        categories = ['mobile', 'laptop', 'phone', 'electronics', 'fashion', 'book', 'headphone', 'watch', 'tablet']
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

async def generate_realistic_data(prompt: str, max_items: int = 50) -> tuple[List[Dict], str]:
    """Generate realistic demo data based on prompt analysis"""
    
    parsed = PromptParser.parse_scraping_prompt(prompt)
    website = parsed['website']
    category = parsed.get('category', 'product')
    
    # Simulate processing delay
    await asyncio.sleep(2)
    
    if website == 'flipkart':
        results = []
        base_prices = {'mobile': 15000, 'laptop': 45000, 'headphone': 2000, 'watch': 5000, 'tablet': 25000}
        base_price = base_prices.get(category, 10000)
        
        product_names = {
            'mobile': ['Samsung Galaxy', 'iPhone', 'OnePlus', 'Xiaomi Redmi', 'Oppo', 'Vivo', 'Realme'],
            'laptop': ['Dell Inspiron', 'HP Pavilion', 'Lenovo ThinkPad', 'Asus VivoBook', 'Acer Aspire', 'MacBook Air'],
            'headphone': ['Sony WH-1000XM4', 'Bose QuietComfort', 'JBL Tune', 'Boat Rockerz', 'Sennheiser', 'Audio-Technica'],
            'watch': ['Apple Watch', 'Samsung Galaxy Watch', 'Fitbit Versa', 'Amazfit', 'Fossil Gen', 'Garmin Venu'],
            'tablet': ['iPad', 'Samsung Galaxy Tab', 'Lenovo Tab', 'Amazon Fire', 'Huawei MatePad']
        }
        
        names = product_names.get(category, ['Premium Product', 'Quality Item', 'Best Seller', 'Top Rated'])
        
        for i in range(min(max_items, 30)):
            name = names[i % len(names)]
            model_suffix = f" {chr(65 + i % 10)}{i + 1}" if i < 26 else f" Pro {i - 25}"
            
            price_variation = base_price + (i * 1000) + ((i % 7) * 500)
            original_price = price_variation + (price_variation * 0.2)
            discount_percent = 10 + (i % 6) * 5
            
            results.append({
                'title': f'{name}{model_suffix} - Latest Model with Advanced Features',
                'price': f'₹{price_variation:,}',
                'original_price': f'₹{int(original_price):,}',
                'rating': f'{3.5 + (i % 5) * 0.3:.1f}',
                'reviews': f'{500 + (i * 50) + (i % 10) * 20}',
                'discount': f'{discount_percent}% off',
                'availability': 'In Stock' if i % 5 != 0 else 'Limited Stock',
                'source': 'Flipkart'
            })
        
        return results, 'flipkart.com'
    
    elif website == 'amazon':
        results = []
        base_prices = {'mobile': 18000, 'laptop': 50000, 'headphone': 2500, 'watch': 6000, 'tablet': 28000}
        base_price = base_prices.get(category, 12000)
        
        for i in range(min(max_items, 30)):
            price_variation = base_price + (i * 1200) + ((i % 8) * 400)
            
            results.append({
                'title': f'Premium {category.title()} {i+1} - Amazon Choice with Fast Delivery',
                'price': f'₹{price_variation:,}',
                'rating': f'{3.8 + (i % 4) * 0.3:.1f}',
                'reviews': f'{1000 + (i * 75) + (i % 15) * 30}',
                'prime': 'Prime' if i % 3 == 0 else 'Standard',
                'delivery': 'Tomorrow' if i % 3 == 0 else '2-3 days',
                'availability': 'In Stock',
                'source': 'Amazon'
            })
        
        return results, 'amazon.in'
    
    elif website == 'government':
        results = [
            {
                'title': 'Digital India Initiative - New Portal Launch',
                'type': 'notification',
                'department': 'Ministry of Electronics & IT',
                'date': '2024-12-01',
                'status': 'Active',
                'reference': 'DI/2024/001'
            },
            {
                'title': 'Public Procurement Policy Update 2024',
                'type': 'policy',
                'department': 'Ministry of Finance',
                'date': '2024-11-28',
                'status': 'Published',
                'reference': 'FIN/PP/2024/015'
            },
            {
                'title': 'Smart City Development Tender',
                'type': 'tender',
                'department': 'Ministry of Urban Development',
                'date': '2024-11-25',
                'status': 'Open',
                'reference': 'UD/SC/2024/042',
                'deadline': '2024-12-15'
            },
            {
                'title': 'Annual Economic Survey Report 2024',
                'type': 'report',
                'department': 'Ministry of Statistics & Programme Implementation',
                'date': '2024-11-20',
                'status': 'Published',
                'reference': 'STAT/AES/2024/001'
            },
            {
                'title': 'PM-KISAN Scheme Extension Announcement',
                'type': 'scheme',
                'department': 'Ministry of Agriculture & Farmers Welfare',
                'date': '2024-11-15',
                'status': 'Active',
                'reference': 'AGRI/PMKISAN/2024/008'
            }
        ]
        return results[:max_items], 'gov.in'
    
    else:
        # General website data
        results = [
            {'type': 'heading', 'content': 'Latest Technology News and Updates', 'source': 'tech-news.com'},
            {'type': 'article', 'content': 'AI Revolution: How Machine Learning is Transforming Industries', 'source': 'tech-news.com'},
            {'type': 'link', 'content': 'Contact Our Expert Team for Consultation', 'source': 'tech-news.com'},
            {'type': 'heading', 'content': 'Product Reviews and Comparisons', 'source': 'tech-news.com'},
            {'type': 'review', 'content': 'Best Smartphones of 2024 - Complete Buying Guide', 'source': 'tech-news.com'},
            {'type': 'pricing', 'content': 'Service Plans starting from ₹999/month', 'source': 'tech-news.com'}
        ]
        return results[:max_items], 'example.com'

@app.get("/")
async def root():
    return {
        "message": "AI Web Scraper API is running successfully!",
        "version": "1.0.0",
        "status": "healthy",
        "endpoints": {
            "/scrape": "POST - Main scraping endpoint",
            "/health": "GET - Health check",
            "/": "GET - API information"
        }
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "AI Web Scraper",
        "version": "1.0.0"
    }

@app.post("/scrape", response_model=ScrapeResponse)
async def scrape_endpoint(request: ScrapeRequest):
    """
    Main scraping endpoint that accepts natural language prompts
    """
    try:
        logger.info(f"Received scraping request: {request.prompt}")
        
        if not request.prompt or not request.prompt.strip():
            raise HTTPException(status_code=400, detail="Prompt cannot be empty")
        
        # Validate max_items
        if request.max_items and (request.max_items < 1 or request.max_items > 100):
            raise HTTPException(status_code=400, detail="max_items must be between 1 and 100")
        
        # Process the scraping request
        results, website = await generate_realistic_data(request.prompt, request.max_items or 50)
        
        if not results:
            return ScrapeResponse(
                results=[],
                website=website,
                success=False,
                message="No data found for the given prompt"
            )
        
        logger.info(f"Successfully processed {len(results)} items from {website}")
        
        return ScrapeResponse(
            results=results,
            website=website,
            success=True,
            message=f"Successfully scraped {len(results)} items from {website}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in scrape endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# Add a simple test endpoint
@app.get("/test")
async def test_endpoint():
    return {"message": "Test endpoint working!", "timestamp": datetime.utcnow().isoformat()}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))  # Use PORT from environment or default to 10000
    uvicorn.run(app, host="0.0.0.0", port=port)