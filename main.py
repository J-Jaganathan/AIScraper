import re
import json
import asyncio
from playwright.async_api import Page, Response
from playwright.async_api import async_playwright   
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from typing import List, Dict, Optional, Tuple
from urllib.parse import urlparse, urljoin
from dataclasses import dataclass
from enum import Enum
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class ContentType(str, Enum):
    PRODUCTS = "products"
    NEWS = "news"
    JOBS = "jobs"
    REVIEWS = "reviews"
    CONTACTS = "contacts"
    PRICES = "prices"
    TABLES = "tables"
    FORMS = "forms"
    IMAGES = "images"
    DOCUMENTS = "documents"
    SOCIAL_MEDIA = "social_media"
    REAL_ESTATE = "real_estate"
    EVENTS = "events"
    GENERAL = "general"

@dataclass
class WebsiteInfo:
    url: str
    domain: str
    site_type: str
    content_type: ContentType
    complexity: str
    requires_js: bool
    estimated_load_time: int
    login_required: bool = False
    form_interactions: List[str] = None
    expected_data_structure: Dict = None
    confidence_score: float = 0.0

class IntelligentPromptParser:
    """AI-powered prompt parser that can understand complex natural language requests"""
    
    # Comprehensive website patterns
    WEBSITE_PATTERNS = {
        'ecommerce': {
            'amazon': ['amazon.in', 'amazon.com', 'amazon.co.uk', 'amazon.de', 'amazon'],
            'flipkart': ['flipkart.com', 'flipkart'],
            'myntra': ['myntra.com', 'myntra'],
            'snapdeal': ['snapdeal.com', 'snapdeal'],
            'nykaa': ['nykaa.com', 'nykaa'],
            'ajio': ['ajio.com', 'ajio'],
            'ebay': ['ebay.com', 'ebay.in', 'ebay'],
            'shopify': ['shopify.com', 'myshopify.com'],
            'etsy': ['etsy.com', 'etsy'],
            'alibaba': ['alibaba.com', 'alibaba'],
            'bigbasket': ['bigbasket.com', 'bigbasket'],
            'grofers': ['grofers.com', 'blinkit.com', 'grofers', 'blinkit'],
            'swiggy': ['swiggy.com', 'swiggy'],
            'zomato': ['zomato.com', 'zomato'],
            'paytm': ['paytm.com', 'paytm'],
            'shopclues': ['shopclues.com', 'shopclues']
        },
        'news': {
            'times': ['timesofindia.com', 'times of india', 'toi'],
            'hindu': ['thehindu.com', 'the hindu'],
            'ndtv': ['ndtv.com', 'ndtv'],
            'indianexpress': ['indianexpress.com', 'indian express'],
            'hindustantimes': ['hindustantimes.com', 'hindustan times'],
            'livemint': ['livemint.com', 'mint'],
            'businessstandard': ['business-standard.com', 'business standard'],
            'economictimes': ['economictimes.com', 'et', 'economic times'],
            'moneycontrol': ['moneycontrol.com', 'moneycontrol'],
            'cnn': ['cnn.com', 'cnn'],
            'bbc': ['bbc.com', 'bbc.co.uk', 'bbc'],
            'reuters': ['reuters.com', 'reuters'],
            'bloomberg': ['bloomberg.com', 'bloomberg'],
            'techcrunch': ['techcrunch.com', 'techcrunch'],
            'theverge': ['theverge.com', 'the verge']
        },
        'jobs': {
            'naukri': ['naukri.com', 'naukri'],
            'linkedin': ['linkedin.com', 'linkedin'],
            'indeed': ['indeed.com', 'indeed.co.in', 'indeed'],
            'monster': ['monster.com', 'monsterindia.com', 'monster'],
            'shine': ['shine.com', 'shine'],
            'glassdoor': ['glassdoor.com', 'glassdoor.co.in', 'glassdoor'],
            'upwork': ['upwork.com', 'upwork'],
            'freelancer': ['freelancer.com', 'freelancer'],
            'fiverr': ['fiverr.com', 'fiverr'],
            'angel': ['angel.co', 'angellist.com', 'angel list'],
            'dice': ['dice.com', 'dice'],
            'stackoverflow': ['stackoverflow.com/jobs', 'stack overflow jobs']
        },
        'government': {
            'india': ['gov.in', 'government', 'ministry', 'govt'],
            'tenders': ['tender', 'eprocurement', 'gem.gov.in', 'etender'],
            'ssc': ['ssc.nic.in', 'ssc'],
            'upsc': ['upsc.gov.in', 'upsc'],
            'railway': ['indianrailways.gov.in', 'railway', 'irctc'],
            'postal': ['indiapost.gov.in', 'india post'],
            'psu': ['ongc.co.in', 'iocl.com', 'ntpc.co.in', 'sail.co.in']
        },
        'real_estate': {
            'magicbricks': ['magicbricks.com', 'magicbricks'],
            'housing': ['housing.com', 'housing'],
            'commonfloor': ['commonfloor.com', 'commonfloor'],
            'makaan': ['makaan.com', 'makaan'],
            'proptiger': ['proptiger.com', 'proptiger'],
            'zillow': ['zillow.com', 'zillow'],
            'realtor': ['realtor.com', 'realtor'],
            'redfin': ['redfin.com', 'redfin']
        },
        'education': {
            'coursera': ['coursera.org', 'coursera'],
            'udemy': ['udemy.com', 'udemy'],
            'edx': ['edx.org', 'edx'],
            'khan': ['khanacademy.org', 'khan academy'],
            'byju': ['byjus.com', 'byjus'],
            'unacademy': ['unacademy.com', 'unacademy'],
            'vedantu': ['vedantu.com', 'vedantu']
        },
        'travel': {
            'makemytrip': ['makemytrip.com', 'makemytrip'],
            'goibibo': ['goibibo.com', 'goibibo'],
            'cleartrip': ['cleartrip.com', 'cleartrip'],
            'yatra': ['yatra.com', 'yatra'],
            'booking': ['booking.com', 'booking'],
            'airbnb': ['airbnb.com', 'airbnb'],
            'expedia': ['expedia.com', 'expedia'],
            'trivago': ['trivago.com', 'trivago']
        },
        'social': {
            'facebook': ['facebook.com', 'facebook'],
            'instagram': ['instagram.com', 'instagram'],
            'twitter': ['twitter.com', 'x.com', 'twitter'],
            'linkedin': ['linkedin.com', 'linkedin'],
            'youtube': ['youtube.com', 'youtube'],
            'reddit': ['reddit.com', 'reddit'],
            'quora': ['quora.com', 'quora'],
            'pinterest': ['pinterest.com', 'pinterest']
        }
    }
    
    # Advanced content type detection
    CONTENT_PATTERNS = {
        ContentType.PRODUCTS: [
            'product', 'item', 'buy', 'purchase', 'shop', 'store', 'price', 'cart',
            'mobile', 'laptop', 'phone', 'electronics', 'fashion', 'clothes', 'shoes',
            'book', 'furniture', 'appliance', 'gadget', 'accessory', 'brand', 'model',
            'specification', 'feature', 'review', 'rating', 'discount', 'offer', 'deal'
        ],
        ContentType.NEWS: [
            'news', 'article', 'breaking', 'headline', 'story', 'report', 'update',
            'latest', 'current', 'today', 'yesterday', 'politics', 'sports', 'business',
            'technology', 'health', 'entertainment', 'world', 'national', 'local'
        ],
        ContentType.JOBS: [
            'job', 'career', 'position', 'opening', 'vacancy', 'hiring', 'recruitment',
            'employment', 'work', 'salary', 'company', 'resume', 'cv', 'interview',
            'skill', 'experience', 'fresher', 'intern', 'manager', 'developer', 'engineer'
        ],
        ContentType.REVIEWS: [
            'review', 'rating', 'feedback', 'opinion', 'comment', 'testimonial',
            'evaluation', 'assessment', 'critique', 'recommendation', 'experience',
            'customer', 'user', 'satisfaction', 'quality', 'service'
        ],
        ContentType.CONTACTS: [
            'contact', 'phone', 'email', 'address', 'location', 'office', 'branch',
            'customer service', 'support', 'helpline', 'toll free', 'directory',
            'staff', 'team', 'personnel', 'employee', 'member'
        ],
        ContentType.PRICES: [
            'price', 'cost', 'rate', 'fee', 'charge', 'amount', 'value', 'money',
            'currency', 'dollar', 'rupee', 'euro', 'pound', 'budget', 'expensive',
            'cheap', 'affordable', 'premium', 'discount', 'offer', 'deal'
        ],
        ContentType.TABLES: [
            'table', 'data', 'list', 'record', 'entry', 'row', 'column', 'field',
            'database', 'spreadsheet', 'chart', 'graph', 'statistics', 'report',
            'summary', 'comparison', 'analysis', 'result'
        ],
        ContentType.REAL_ESTATE: [
            'property', 'house', 'apartment', 'flat', 'villa', 'plot', 'land',
            'rent', 'sale', 'buy', 'lease', 'mortgage', 'broker', 'agent',
            'bedroom', 'bathroom', 'kitchen', 'parking', 'amenity', 'location'
        ],
        ContentType.EVENTS: [
            'event', 'conference', 'seminar', 'workshop', 'meeting', 'webinar',
            'concert', 'show', 'festival', 'exhibition', 'fair', 'competition',
            'tournament', 'match', 'game', 'date', 'time', 'venue', 'registration'
        ]
    }
    
    # Intent detection patterns
    INTENT_PATTERNS = {
        'extract_all': ['all', 'everything', 'complete', 'entire', 'full', 'total'],
        'extract_specific': ['specific', 'particular', 'certain', 'selected', 'only'],
        'compare': ['compare', 'comparison', 'versus', 'vs', 'difference', 'better'],
        'filter': ['filter', 'where', 'condition', 'criteria', 'requirement'],
        'sort': ['sort', 'order', 'arrange', 'rank', 'top', 'best', 'lowest', 'highest'],
        'count': ['count', 'number', 'total', 'how many', 'quantity'],
        'latest': ['latest', 'recent', 'new', 'current', 'today', 'this week', 'this month'],
        'search': ['search', 'find', 'look for', 'get', 'fetch', 'retrieve']
    }
    
    @classmethod
    def parse_comprehensive_prompt(cls, prompt: str) -> Dict:
        """
        Comprehensive prompt parsing with AI-like understanding
        Returns complete scraping strategy
        """
        prompt_lower = prompt.lower().strip()
        
        # Step 1: Extract direct URLs
        direct_urls = cls._extract_urls(prompt)
        
        # Step 2: Identify content type
        content_type = cls._identify_content_type(prompt_lower)
        
        # Step 3: Identify target websites
        target_websites = cls._identify_target_websites(prompt_lower, content_type)
        
        # Step 4: Add direct URLs to target websites
        for url in direct_urls:
            domain = urlparse(url).netloc
            target_websites.append(WebsiteInfo(
                url=url,
                domain=domain,
                site_type=cls._classify_site_type(domain),
                content_type=content_type,
                complexity='dynamic',
                requires_js=True,
                estimated_load_time=5,
                confidence_score=1.0
            ))
        
        # Step 5: Identify extraction requirements
        extraction_requirements = cls._identify_extraction_requirements(prompt_lower, content_type)
        
        # Step 6: Identify filters and conditions
        filters = cls._identify_filters(prompt_lower)
        
        # Step 7: Identify intent
        intent = cls._identify_intent(prompt_lower)
        
        return {
            'target_websites': target_websites,
            'content_type': content_type,
            'extraction_requirements': extraction_requirements,
            'filters': filters,
            'intent': intent,
            'original_prompt': prompt,
            'confidence_score': cls._calculate_overall_confidence(target_websites)
        }
    
    @classmethod
    def _extract_urls(cls, prompt: str) -> List[str]:
        """Extract all URLs from prompt"""
        # Enhanced URL pattern
        url_pattern = re.compile(
            r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        )
        urls = url_pattern.findall(prompt)
        
        # Extract domain-like patterns
        domain_pattern = re.compile(
            r'\b(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\b'
        )
        potential_domains = domain_pattern.findall(prompt.lower())
        
        # Validate and add http to domains
        for domain in potential_domains:
            if ('.' in domain and 
                len(domain.split('.')[-1]) >= 2 and 
                domain not in ['e.g', 'i.e', 'etc.com'] and
                not domain.endswith('.txt') and
                not domain.endswith('.pdf')):
                if not domain.startswith('http'):
                    urls.append(f"https://{domain}")
        
        return list(set(urls))
    
    @classmethod
    def _identify_content_type(cls, prompt: str) -> ContentType:
        """Identify what type of content user wants to extract"""
        content_scores = {}
        
        for content_type, keywords in cls.CONTENT_PATTERNS.items():
            score = sum(1 for keyword in keywords if keyword in prompt)
            if score > 0:
                content_scores[content_type] = score
        
        if content_scores:
            return max(content_scores, key=content_scores.get)
        
        return ContentType.GENERAL
    
    @classmethod
    def _identify_target_websites(cls, prompt: str, content_type: ContentType) -> List[WebsiteInfo]:
        """Identify target websites based on context and content type"""
        websites = []
        
        # Direct website name matching
        for category, sites in cls.WEBSITE_PATTERNS.items():
            for site_name, patterns in sites.items():
                for pattern in patterns:
                    if pattern in prompt:
                        url = cls._construct_search_url(site_name, prompt, content_type)
                        if url:
                            websites.append(WebsiteInfo(
                                url=url,
                                domain=site_name,
                                site_type=category,
                                content_type=content_type,
                                complexity='dynamic' if category in ['ecommerce', 'social'] else 'simple',
                                requires_js=category in ['ecommerce', 'social', 'jobs'],
                                estimated_load_time=10 if category == 'ecommerce' else 5,
                                confidence_score=0.9
                            ))
        
        # If no specific sites found, infer from content type
        if not websites:
            websites = cls._infer_websites_from_content_type(content_type, prompt)
        
        return websites[:5]  # Limit to 5 websites
    
    @classmethod
    def _construct_search_url(cls, site_name: str, prompt: str, content_type: ContentType) -> Optional[str]:
        """Construct intelligent search URLs based on site and content type"""
        search_terms = cls._extract_search_terms(prompt)
        search_query = "+".join(search_terms[:5])
        encoded_query = search_query.replace(" ", "+")
        
        url_templates = {
            # E-commerce sites
            'amazon': f"https://www.amazon.in/s?k={encoded_query}",
            'flipkart': f"https://www.flipkart.com/search?q={encoded_query}",
            'myntra': f"https://www.myntra.com/{encoded_query}",
            'ebay': f"https://www.ebay.in/sch/i.html?_nkw={encoded_query}",
            'etsy': f"https://www.etsy.com/search?q={encoded_query}",
            'shopify': f"https://www.shopify.com/search?q={encoded_query}",
            
            # Job sites
            'naukri': f"https://www.naukri.com/jobs-in-india?k={encoded_query}",
            'linkedin': f"https://www.linkedin.com/jobs/search/?keywords={encoded_query}",
            'indeed': f"https://www.indeed.co.in/jobs?q={encoded_query}",
            'monster': f"https://www.monsterindia.com/search/{encoded_query}-jobs",
            'glassdoor': f"https://www.glassdoor.co.in/Job/jobs.htm?sc.keyword={encoded_query}",
            
            # News sites
            'times': f"https://timesofindia.indiatimes.com/topic/{encoded_query}",
            'hindu': f"https://www.thehindu.com/search/?q={encoded_query}",
            'ndtv': f"https://www.ndtv.com/search?searchtext={encoded_query}",
            'cnn': f"https://www.cnn.com/search?q={encoded_query}",
            'bbc': f"https://www.bbc.com/search?q={encoded_query}",
            
            # Real estate
            'magicbricks': f"https://www.magicbricks.com/property-for-sale/residential-real-estate?keyword={encoded_query}",
            'housing': f"https://housing.com/in/search?q={encoded_query}",
            'zillow': f"https://www.zillow.com/homes/{encoded_query}_rb/",
            
            # Travel
            'makemytrip': f"https://www.makemytrip.com/search?q={encoded_query}",
            'booking': f"https://www.booking.com/searchresults.html?ss={encoded_query}",
            'airbnb': f"https://www.airbnb.com/s/{encoded_query}",
            
            # Education
            'coursera': f"https://www.coursera.org/search?query={encoded_query}",
            'udemy': f"https://www.udemy.com/courses/search/?q={encoded_query}",
            'edx': f"https://www.edx.org/search?q={encoded_query}",
            
            # Default fallback
            'default': f"https://www.google.com/search?q={encoded_query}"
        }
        
        return url_templates.get(site_name, url_templates['default'])
    
    @classmethod
    def _extract_search_terms(cls, prompt: str) -> List[str]:
        """Extract meaningful search terms from prompt"""
        # Enhanced stop words
        stop_words = {
            'get', 'find', 'search', 'scrape', 'extract', 'from', 'in', 'on', 'with', 
            'and', 'or', 'the', 'a', 'an', 'to', 'for', 'of', 'at', 'by', 'is', 'are',
            'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did',
            'will', 'would', 'could', 'should', 'may', 'might', 'can', 'all', 'any',
            'some', 'many', 'few', 'most', 'more', 'less', 'than', 'this', 'that',
            'these', 'those', 'here', 'there', 'where', 'when', 'why', 'how', 'what',
            'who', 'which', 'whose', 'whom', 'website', 'site', 'page', 'data',
            'information', 'details', 'list', 'items', 'content'
        }
        
        # Extract words and phrases
        words = re.findall(r'\b[a-zA-Z]+\b', prompt.lower())
        meaningful_words = [
            word for word in words 
            if word not in stop_words and len(word) > 2
        ]
        
        # Extract quoted phrases
        quoted_phrases = re.findall(r'"([^"]*)"', prompt)
        meaningful_words.extend(quoted_phrases)
        
        return meaningful_words[:10]  # Limit to 10 terms
    
    @classmethod
    def _infer_websites_from_content_type(cls, content_type: ContentType, prompt: str) -> List[WebsiteInfo]:
        """Infer relevant websites based on content type"""
        websites = []
        search_terms = cls._extract_search_terms(prompt)
        
        if content_type == ContentType.PRODUCTS:
            # Major e-commerce sites
            ecommerce_sites = [
                ('amazon', 'https://www.amazon.in/s?k=', 'ecommerce'),
                ('flipkart', 'https://www.flipkart.com/search?q=', 'ecommerce'),
                ('myntra', 'https://www.myntra.com/search?q=', 'ecommerce'),
                ('ebay', 'https://www.ebay.in/sch/i.html?_nkw=', 'ecommerce')
            ]
            
            for site_name, base_url, site_type in ecommerce_sites:
                search_query = "+".join(search_terms[:3])
                websites.append(WebsiteInfo(
                    url=f"{base_url}{search_query}",
                    domain=site_name,
                    site_type=site_type,
                    content_type=content_type,
                    complexity='dynamic',
                    requires_js=True,
                    estimated_load_time=10,
                    confidence_score=0.8
                ))
        
        elif content_type == ContentType.JOBS:
            job_sites = [
                ('naukri', 'https://www.naukri.com/jobs-in-india?k=', 'jobs'),
                ('linkedin', 'https://www.linkedin.com/jobs/search/?keywords=', 'jobs'),
                ('indeed', 'https://www.indeed.co.in/jobs?q=', 'jobs')
            ]
            
            for site_name, base_url, site_type in job_sites:
                search_query = "+".join(search_terms[:3])
                websites.append(WebsiteInfo(
                    url=f"{base_url}{search_query}",
                    domain=site_name,
                    site_type=site_type,
                    content_type=content_type,
                    complexity='dynamic',
                    requires_js=True,
                    estimated_load_time=8,
                    confidence_score=0.8
                ))
        
        elif content_type == ContentType.NEWS:
            news_sites = [
                ('times', 'https://timesofindia.indiatimes.com/', 'news'),
                ('hindu', 'https://www.thehindu.com/', 'news'),
                ('ndtv', 'https://www.ndtv.com/', 'news')
            ]
            
            for site_name, base_url, site_type in news_sites:
                websites.append(WebsiteInfo(
                    url=base_url,
                    domain=site_name,
                    site_type=site_type,
                    content_type=content_type,
                    complexity='simple',
                    requires_js=False,
                    estimated_load_time=3,
                    confidence_score=0.7
                ))
        
        elif content_type == ContentType.REAL_ESTATE:
            real_estate_sites = [
                ('magicbricks', 'https://www.magicbricks.com/', 'real_estate'),
                ('housing', 'https://housing.com/', 'real_estate'),
                ('commonfloor', 'https://www.commonfloor.com/', 'real_estate')
            ]
            
            for site_name, base_url, site_type in real_estate_sites:
                websites.append(WebsiteInfo(
                    url=base_url,
                    domain=site_name,
                    site_type=site_type,
                    content_type=content_type,
                    complexity='dynamic',
                    requires_js=True,
                    estimated_load_time=8,
                    confidence_score=0.7
                ))
        
        return websites
    
    @classmethod
    def _identify_extraction_requirements(cls, prompt: str, content_type: ContentType) -> Dict:
        """Identify what specific data fields to extract"""
        requirements = {
            'fields': [],
            'include_images': False,
            'include_links': False,
            'include_metadata': True,
            'max_items': 50,
            'data_format': 'json'
        }
        
        # Field extraction based on content type
        if content_type == ContentType.PRODUCTS:
            requirements['fields'] = ['title', 'price', 'rating', 'description', 'availability']
        elif content_type == ContentType.JOBS:
            requirements['fields'] = ['title', 'company', 'location', 'salary', 'experience', 'skills']
        elif content_type == ContentType.NEWS:
            requirements['fields'] = ['headline', 'summary', 'author', 'published_date', 'category']
        elif content_type == ContentType.CONTACTS:
            requirements['fields'] = ['name', 'phone', 'email', 'address', 'designation']
        elif content_type == ContentType.REAL_ESTATE:
            requirements['fields'] = ['title', 'price', 'location', 'area', 'bedrooms', 'bathrooms']
        elif content_type == ContentType.EVENTS:
            requirements['fields'] = ['title', 'date', 'time', 'venue', 'price', 'description']
        else:
            requirements['fields'] = ['title', 'content', 'url']
        
        # Check for specific field mentions in prompt
        field_patterns = {
            'price': ['price', 'cost', 'rate', 'fee', 'amount', 'money'],
            'title': ['title', 'name', 'heading', 'headline'],
            'description': ['description', 'summary', 'details', 'info'],
            'rating': ['rating', 'review', 'star', 'score'],
            'date': ['date', 'time', 'when', 'schedule'],
            'location': ['location', 'address', 'place', 'where'],
            'contact': ['phone', 'email', 'contact', 'number'],
            'image': ['image', 'photo', 'picture', 'img'],
            'link': ['link', 'url', 'href', 'website']
        }
        
        for field, keywords in field_patterns.items():
            if any(keyword in prompt for keyword in keywords):
                if field not in requirements['fields']:
                    requirements['fields'].append(field)
        
        # Check for special requirements
        if any(word in prompt for word in ['image', 'photo', 'picture']):
            requirements['include_images'] = True
        
        if any(word in prompt for word in ['link', 'url', 'website']):
            requirements['include_links'] = True
        
        # Extract max items if specified
        numbers = re.findall(r'\b(\d+)\b', prompt)
        if numbers:
            max_items = int(numbers[-1])  # Take the last number mentioned
            if 1 <= max_items <= 1000:
                requirements['max_items'] = max_items
        
        # Check for output format
        if any(word in prompt for word in ['csv', 'excel', 'spreadsheet']):
            requirements['data_format'] = 'csv'
        elif any(word in prompt for word in ['json', 'api']):
            requirements['data_format'] = 'json'
        
        return requirements
    
    @classmethod
    def _identify_filters(cls, prompt: str) -> Dict:
        """Identify filters and conditions from prompt"""
        filters = {
            'price_range': None,
            'rating_min': None,
            'location': [],
            'keywords': [],
            'exclude_keywords': [],
            'date_range': None,
            'category': None
        }
        
        # Price range extraction
        price_patterns = [
            r'under\s*(\d+)', r'below\s*(\d+)', r'less\s*than\s*(\d+)',
            r'above\s*(\d+)', r'over\s*(\d+)', r'more\s*than\s*(\d+)',
            r'between\s*(\d+)\s*(?:and|to)\s*(\d+)',
            r'(\d+)\s*(?:to|-)\s*(\d+)'
        ]
        
        for pattern in price_patterns:
            match = re.search(pattern, prompt)
            if match:
                groups = match.groups()
                if len(groups) == 1:
                    if 'under' in pattern or 'below' in pattern or 'less' in pattern:
                        filters['price_range'] = {'max': int(groups[0])}
                    else:
                        filters['price_range'] = {'min': int(groups[0])}
                elif len(groups) == 2:
                    filters['price_range'] = {'min': int(groups[0]), 'max': int(groups[1])}
                break
        
        # Rating extraction
        rating_match = re.search(r'rating\s*(?:above|over|more than)\s*(\d+(?:\.\d+)?)', prompt)
        if rating_match:
            filters['rating_min'] = float(rating_match.group(1))
        
        # Location extraction
        location_patterns = [
            r'in\s+([A-Za-z\s]+)', r'from\s+([A-Za-z\s]+)', r'at\s+([A-Za-z\s]+)',
            r'near\s+([A-Za-z\s]+)', r'around\s+([A-Za-z\s]+)'
        ]
        
        for pattern in location_patterns:
            matches = re.findall(pattern, prompt)
            filters['location'].extend(matches)
        
        # Keyword extraction (excluding common stop words)
        exclude_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        words = re.findall(r'\b[A-Za-z]{3,}\b', prompt.lower())
        filters['keywords'] = [word for word in words if word not in exclude_words][:10]
        
        return filters
    
    @classmethod
    def _identify_intent(cls, prompt: str) -> str:
        """Identify user's main intent"""
        for intent, keywords in cls.INTENT_PATTERNS.items():
            if any(keyword in prompt.lower() for keyword in keywords):
                return intent
        return 'search'
    
    @classmethod
    def _classify_site_type(cls, domain: str) -> str:
        """Classify website type based on domain"""
        for category, sites in cls.WEBSITE_PATTERNS.items():
            for site_name, patterns in sites.items():
                if any(pattern in domain.lower() for pattern in patterns):
                    return category
        return 'general'
    
    @classmethod
    def _calculate_overall_confidence(cls, websites: List[WebsiteInfo]) -> float:
        """Calculate overall confidence score"""
        if not websites:
            return 0.0
        return sum(site.confidence_score for site in websites) / len(websites)


class StealthScraper:
    """Advanced stealth scraper with anti-bot detection"""
    
    def __init__(self):
        self.browser = None
        self.context = None
        self.max_retries = 3
        self.retry_delay = 2
        
    async def __aenter__(self):
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.cleanup()
    
    async def initialize(self):
        """Initialize browser with stealth configuration"""
        from playwright.async_api import async_playwright
        
        self.playwright = await async_playwright().start()
        
        # Advanced browser configuration for stealth
        self.browser = await self.playwright.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--no-first-run',
                '--no-zygote',
                '--disable-gpu',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor',
                '--disable-background-timer-throttling',
                '--disable-renderer-backgrounding',
                '--disable-backgrounding-occluded-windows',
                '--disable-ipc-flooding-protection'
            ]
        )
        
        # Create stealth context
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            extra_http_headers={
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
        )
        
        # Block unnecessary resources
        await self.context.route('**/*', self._handle_route)
        
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
            
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
        """)
    
    async def _handle_route(self, route):
        """Handle route blocking for performance"""
        resource_type = route.request.resource_type
        
        # Block unnecessary resources
        if resource_type in ['image', 'stylesheet', 'font', 'media']:
            await route.abort()
        else:
            await route.continue_()
    
    async def cleanup(self):
        """Clean up browser resources"""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if hasattr(self, 'playwright'):
            await self.playwright.stop()
    
    async def scrape_website(self, website_info: WebsiteInfo, extraction_requirements: Dict) -> List[Dict]:
        """Scrape a single website with intelligent content extraction"""
        results = []
        
        for attempt in range(self.max_retries):
            try:
                page = await self.context.new_page()
                
                # Navigate with timeout
                await page.goto(website_info.url, wait_until='domcontentloaded', timeout=30000)
                
                # Wait for dynamic content
                if website_info.requires_js:
                    await page.wait_for_timeout(3000)
                
                # Extract data based on content type
                if website_info.content_type == ContentType.PRODUCTS:
                    results = await self._extract_products(page, extraction_requirements)
                elif website_info.content_type == ContentType.JOBS:
                    results = await self._extract_jobs(page, extraction_requirements)
                elif website_info.content_type == ContentType.NEWS:
                    results = await self._extract_news(page, extraction_requirements)
                elif website_info.content_type == ContentType.REAL_ESTATE:
                    results = await self._extract_real_estate(page, extraction_requirements)
                else:
                    results = await self._extract_general_content(page, extraction_requirements)
                
                # Add metadata to each result
                for result in results:
                    result.update({
                        'source_url': website_info.url,
                        'source_domain': website_info.domain,
                        'scraped_at': datetime.now().isoformat(),
                        'confidence_score': website_info.confidence_score
                    })
                
                await page.close()
                
                if results:
                    logger.info(f"Successfully scraped {len(results)} items from {website_info.domain}")
                    break
                else:
                    logger.warning(f"No data extracted from {website_info.domain} on attempt {attempt + 1}")
                    
            except Exception as e:
                logger.error(f"Error scraping {website_info.url} (attempt {attempt + 1}): {str(e)}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (2 ** attempt))
                else:
                    logger.error(f"Failed to scrape {website_info.url} after {self.max_retries} attempts")
        
        return results
    
    async def _extract_products(self, page, requirements: Dict) -> List[Dict]:
        """Extract product information from e-commerce sites"""
        products = []
        
        # Common product selectors for different sites
        product_selectors = [
            '[data-testid*="product"]',
            '.product-item', '.product-card', '.product-container',
            '[class*="product"]', '[id*="product"]',
            '.item', '.listing-item', '.search-result-item',
            '.grid-item', '.tile', '.card'
        ]
        
        # Find product containers
        product_elements = []
        for selector in product_selectors:
            elements = await page.query_selector_all(selector)
            if elements:
                product_elements = elements[:requirements.get('max_items', 50)]
                break
        
        if not product_elements:
            # Fallback: find any repeated structure
            product_elements = await self._find_repeated_elements(page)
        
        for element in product_elements:
            try:
                product = {}
                
                # Extract title
                title_selectors = [
                    'h1', 'h2', 'h3', '[class*="title"]', '[class*="name"]',
                    'a[title]', '.product-title', '.item-title', '[data-testid*="title"]'
                ]
                product['title'] = await self._extract_text_by_selectors(element, title_selectors)
                
                # Extract price
                price_selectors = [
                    '[class*="price"]', '[class*="cost"]', '[class*="amount"]',
                    '.money', '.currency', '[data-testid*="price"]', '.price-current'
                ]
                product['price'] = await self._extract_text_by_selectors(element, price_selectors)
                
                # Extract rating
                rating_selectors = [
                    '[class*="rating"]', '[class*="star"]', '[class*="review"]',
                    '.rating-value', '.star-rating', '[data-testid*="rating"]'
                ]
                product['rating'] = await self._extract_text_by_selectors(element, rating_selectors)
                
                # Extract description
                desc_selectors = [
                    '[class*="description"]', '[class*="summary"]', 'p',
                    '.product-desc', '.item-desc', '[data-testid*="desc"]'
                ]
                product['description'] = await self._extract_text_by_selectors(element, desc_selectors)
                
                # Extract availability
                avail_selectors = [
                    '[class*="stock"]', '[class*="available"]', '[class*="delivery"]',
                    '.availability', '.in-stock', '.out-of-stock'
                ]
                product['availability'] = await self._extract_text_by_selectors(element, avail_selectors)
                
                # Extract image if requested
                if requirements.get('include_images'):
                    img_element = await element.query_selector('img')
                    if img_element:
                        product['image_url'] = await img_element.get_attribute('src')
                
                # Extract link if requested
                if requirements.get('include_links'):
                    link_element = await element.query_selector('a')
                    if link_element:
                        product['product_url'] = await link_element.get_attribute('href')
                
                # Only add if we have meaningful data
                if product.get('title') or product.get('price'):
                    products.append(product)
                    
            except Exception as e:
                logger.debug(f"Error extracting product: {str(e)}")
                continue
        
        return products
    
    async def _extract_jobs(self, page, requirements: Dict) -> List[Dict]:
        """Extract job listings"""
        jobs = []
        
        job_selectors = [
            '[class*="job"]', '[class*="vacancy"]', '[class*="opening"]',
            '.listing-item', '.search-result', '.job-card', '.job-item',
            '[data-testid*="job"]', '.position', '.role'
        ]
        
        job_elements = []
        for selector in job_selectors:
            elements = await page.query_selector_all(selector)
            if elements:
                job_elements = elements[:requirements.get('max_items', 50)]
                break
        
        if not job_elements:
            job_elements = await self._find_repeated_elements(page)
        
        for element in job_elements:
            try:
                job = {}
                
                # Job title
                title_selectors = [
                    'h1', 'h2', 'h3', '[class*="title"]', '[class*="role"]',
                    '.job-title', '.position-title', 'a[title]'
                ]
                job['title'] = await self._extract_text_by_selectors(element, title_selectors)
                
                # Company
                company_selectors = [
                    '[class*="company"]', '[class*="employer"]', '[class*="organization"]',
                    '.company-name', '.employer-name', '[data-testid*="company"]'
                ]
                job['company'] = await self._extract_text_by_selectors(element, company_selectors)
                
                # Location
                location_selectors = [
                    '[class*="location"]', '[class*="city"]', '[class*="place"]',
                    '.job-location', '.location-name', '[data-testid*="location"]'
                ]
                job['location'] = await self._extract_text_by_selectors(element, location_selectors)
                
                # Salary
                salary_selectors = [
                    '[class*="salary"]', '[class*="pay"]', '[class*="wage"]',
                    '.compensation', '.salary-range', '[data-testid*="salary"]'
                ]
                job['salary'] = await self._extract_text_by_selectors(element, salary_selectors)
                
                # Experience
                exp_selectors = [
                    '[class*="experience"]', '[class*="exp"]', '[class*="year"]',
                    '.experience-required', '.years-exp'
                ]
                job['experience'] = await self._extract_text_by_selectors(element, exp_selectors)
                
                # Skills
                skill_selectors = [
                    '[class*="skill"]', '[class*="tech"]', '[class*="requirement"]',
                    '.skills-required', '.technologies'
                ]
                job['skills'] = await self._extract_text_by_selectors(element, skill_selectors)
                
                if job.get('title') or job.get('company'):
                    jobs.append(job)
                    
            except Exception as e:
                logger.debug(f"Error extracting job: {str(e)}")
                continue
        
        return jobs
    
    async def _extract_news(self, page, requirements: Dict) -> List[Dict]:
        """Extract news articles"""
        articles = []
        
        article_selectors = [
            'article', '[class*="article"]', '[class*="news"]', '[class*="story"]',
            '.post', '.entry', '.content-item', '[data-testid*="article"]',
            '.headline-item', '.news-item'
        ]
        
        article_elements = []
        for selector in article_selectors:
            elements = await page.query_selector_all(selector)
            if elements:
                article_elements = elements[:requirements.get('max_items', 50)]
                break
        
        if not article_elements:
            article_elements = await self._find_repeated_elements(page)
        
        for element in article_elements:
            try:
                article = {}
                
                # Headline
                headline_selectors = [
                    'h1', 'h2', 'h3', '[class*="headline"]', '[class*="title"]',
                    '.article-title', '.news-title', 'a[title]'
                ]
                article['headline'] = await self._extract_text_by_selectors(element, headline_selectors)
                
                # Summary
                summary_selectors = [
                    '[class*="summary"]', '[class*="excerpt"]', '[class*="description"]',
                    'p', '.lead', '.intro', '.article-summary'
                ]
                article['summary'] = await self._extract_text_by_selectors(element, summary_selectors)
                
                # Author
                author_selectors = [
                    '[class*="author"]', '[class*="byline"]', '[class*="writer"]',
                    '.by-author', '.article-author', '[data-testid*="author"]'
                ]
                article['author'] = await self._extract_text_by_selectors(element, author_selectors)
                
                # Published date
                date_selectors = [
                    '[class*="date"]', '[class*="time"]', '[class*="published"]',
                    'time', '.publish-date', '.article-date', '[datetime]'
                ]
                article['published_date'] = await self._extract_text_by_selectors(element, date_selectors)
                
                # Category
                category_selectors = [
                    '[class*="category"]', '[class*="section"]', '[class*="tag"]',
                    '.news-category', '.article-category', '.section-name'
                ]
                article['category'] = await self._extract_text_by_selectors(element, category_selectors)
                
                if article.get('headline'):
                    articles.append(article)
                    
            except Exception as e:
                logger.debug(f"Error extracting article: {str(e)}")
                continue
        
        return articles
    
    async def _extract_real_estate(self, page, requirements: Dict) -> List[Dict]:
        """Extract real estate listings"""
        properties = []
        
        property_selectors = [
            '[class*="property"]', '[class*="listing"]', '[class*="real-estate"]',
            '.property-card', '.listing-item', '.property-item', '.house-card',
            '[data-testid*="property"]', '.property-result'
        ]
        
        property_elements = []
        for selector in property_selectors:
            elements = await page.query_selector_all(selector)
            if elements:
                property_elements = elements[:requirements.get('max_items', 50)]
                break
        
        if not property_elements:
            property_elements = await self._find_repeated_elements(page)
        
        for element in property_elements:
            try:
                property_data = {}
                
                # Title
                title_selectors = [
                    'h1', 'h2', 'h3', '[class*="title"]', '[class*="name"]',
                    '.property-title', '.listing-title', 'a[title]'
                ]
                property_data['title'] = await self._extract_text_by_selectors(element, title_selectors)
                
                # Price
                price_selectors = [
                    '[class*="price"]', '[class*="cost"]', '[class*="rent"]',
                    '.property-price', '.listing-price', '[data-testid*="price"]'
                ]
                property_data['price'] = await self._extract_text_by_selectors(element, price_selectors)
                
                # Location
                location_selectors = [
                    '[class*="location"]', '[class*="address"]', '[class*="area"]',
                    '.property-location', '.listing-location', '.address'
                ]
                property_data['location'] = await self._extract_text_by_selectors(element, location_selectors)
                
                # Area
                area_selectors = [
                    '[class*="area"]', '[class*="size"]', '[class*="sqft"]',
                    '.property-area', '.carpet-area', '.built-area'
                ]
                property_data['area'] = await self._extract_text_by_selectors(element, area_selectors)
                
                # Bedrooms
                bedroom_selectors = [
                    '[class*="bedroom"]', '[class*="bhk"]', '[class*="bed"]',
                    '.bedrooms', '.bhk-info', '[data-testid*="bedroom"]'
                ]
                property_data['bedrooms'] = await self._extract_text_by_selectors(element, bedroom_selectors)
                
                # Bathrooms
                bathroom_selectors = [
                    '[class*="bathroom"]', '[class*="bath"]', '[class*="toilet"]',
                    '.bathrooms', '.bath-info', '[data-testid*="bathroom"]'
                ]
                property_data['bathrooms'] = await self._extract_text_by_selectors(element, bathroom_selectors)
                
                if property_data.get('title') or property_data.get('price'):
                    properties.append(property_data)
                    
            except Exception as e:
                logger.debug(f"Error extracting property: {str(e)}")
                continue
        
        return properties
    
    async def _extract_general_content(self, page, requirements: Dict) -> List[Dict]:
        """Extract general page content"""
        content_items = []
        
        # Try to find structured content first
        structured_selectors = [
            'article', '.post', '.entry', '.content-item', '.card',
            '.item', '.listing', '.result', '[class*="item"]'
        ]
        
        elements = []
        for selector in structured_selectors:
            found_elements = await page.query_selector_all(selector)
            if found_elements:
                elements = found_elements[:requirements.get('max_items', 50)]
                break
        
        # Fallback to paragraphs and headers
        if not elements:
            elements = await page.query_selector_all('p, h1, h2, h3, h4, h5, h6')
            elements = elements[:requirements.get('max_items', 50)]
        
        for element in elements:
            try:
                content = {}
                
                # Extract title (header or first line)
                if await element.evaluate('el => el.tagName.toLowerCase()') in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                    content['title'] = await element.inner_text()
                    content['type'] = 'heading'
                else:
                    title_element = await element.query_selector('h1, h2, h3, h4, h5, h6, [class*="title"]')
                    if title_element:
                        content['title'] = await title_element.inner_text()
                    else:
                        text = await element.inner_text()
                        content['title'] = text[:100] + '...' if len(text) > 100 else text
                    content['type'] = 'content'
                
                # Extract full content
                content['content'] = await element.inner_text()
                
                # Extract URL if it's a link
                if requirements.get('include_links'):
                    link_element = await element.query_selector('a')
                    if link_element:
                        content['url'] = await link_element.get_attribute('href')
                
                if content.get('content') and len(content['content'].strip()) > 10:
                    content_items.append(content)
                    
            except Exception as e:
                logger.debug(f"Error extracting content: {str(e)}")
                continue
        
        return content_items
    
    async def _find_repeated_elements(self, page) -> List:
        """Find repeated elements on the page using pattern detection"""
        try:
            # Get all elements with class or id attributes
            elements = await page.query_selector_all('[class], [id]')
            
            # Group by similar class names
            class_groups = {}
            for element in elements:
                classes = await element.get_attribute('class')
                if classes:
                    # Get the first class name as grouping key
                    first_class = classes.split()[0] if classes.split() else 'unknown'
                    if first_class not in class_groups:
                        class_groups[first_class] = []
                    class_groups[first_class].append(element)
            
            # Find the largest group with meaningful content
            largest_group = []
            max_size = 0
            
            for class_name, group in class_groups.items():
                if len(group) > max_size and len(group) >= 3:  # At least 3 similar elements
                    # Check if elements have meaningful content
                    sample_element = group[0]
                    sample_text = await sample_element.inner_text()
                    if sample_text and len(sample_text.strip()) > 20:
                        largest_group = group
                        max_size = len(group)
            
            return largest_group[:50]  # Limit to 50 elements
            
        except Exception as e:
            logger.debug(f"Error finding repeated elements: {str(e)}")
            return []
    
    async def _extract_text_by_selectors(self, element, selectors: List[str]) -> str:
        """Extract text using multiple selector strategies"""
        for selector in selectors:
            try:
                target_element = await element.query_selector(selector)
                if target_element:
                    text = await target_element.inner_text()
                    if text and text.strip():
                        return text.strip()
            except Exception:
                continue
        return ""


class WebScrapingAPI:
    """FastAPI application for intelligent web scraping"""
    
    def __init__(self):
        self.app = FastAPI(
            title="Intelligent Web Scraper",
            description="AI-powered web scraping with natural language prompts",
            version="1.0.0"
        )
        self.setup_routes()
    
    def setup_routes(self):
        """Setup API routes"""
        
        @self.app.post("/scrape")
        async def scrape_endpoint(request: dict):
            """Main scraping endpoint"""
            try:
                # Parse request
                prompt = request.get('prompt', '')
                max_items = request.get('max_items', 50)
                include_images = request.get('include_images', False)
                output_format = request.get('output_format', 'json')
                
                if not prompt:
                    return {"error": "Prompt is required", "success": False}
                
                # Parse prompt using intelligent parser
                parsed_data = IntelligentPromptParser.parse_comprehensive_prompt(prompt)
                
                # Update extraction requirements
                parsed_data['extraction_requirements']['max_items'] = max_items
                parsed_data['extraction_requirements']['include_images'] = include_images
                parsed_data['extraction_requirements']['data_format'] = output_format
                
                start_time = datetime.now()
                
                # Scrape websites in parallel
                async with StealthScraper() as scraper:
                    tasks = []
                    for website in parsed_data['target_websites']:
                        task = scraper.scrape_website(website, parsed_data['extraction_requirements'])
                        tasks.append(task)
                    
                    if tasks:
                        results = await asyncio.gather(*tasks, return_exceptions=True)
                    else:
                        results = []
                
                # Aggregate results
                all_data = []
                successful_websites = 0
                failed_websites = []
                
                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        failed_websites.append({
                            'url': parsed_data['target_websites'][i].url,
                            'error': str(result)
                        })
                    elif result:
                        all_data.extend(result)
                        successful_websites += 1
                    else:
                        failed_websites.append({
                            'url': parsed_data['target_websites'][i].url,
                            'error': 'No data extracted'
                        })
                
                end_time = datetime.now()
                scraping_time = (end_time - start_time).total_seconds()
                
                # Prepare response metadata
                metadata = {
                    'success': len(all_data) > 0,
                    'record_count': len(all_data),
                    'websites_scraped': successful_websites,
                    'total_websites_attempted': len(parsed_data['target_websites']),
                    'failed_websites': failed_websites,
                    'scraping_time_seconds': scraping_time,
                    'content_type': parsed_data['content_type'].value,
                    'extraction_confidence': parsed_data['confidence_score'],
                    'scraped_at': datetime.now().isoformat()
                }
                
                # Return data in requested format
                if output_format.lower() == 'csv' and all_data:
                    return await self._return_csv(all_data, metadata)
                else:
                    return {
                        'data': all_data,
                        'metadata': metadata
                    }
                    
            except Exception as e:
                logger.error(f"Error in scrape endpoint: {str(e)}")
                return {
                    'error': f"Internal server error: {str(e)}",
                    'success': False,
                    'data': [],
                    'metadata': {
                        'success': False,
                        'record_count': 0,
                        'scraping_time_seconds': 0
                    }
                }
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint"""
            return {"status": "healthy", "timestamp": datetime.now().isoformat()}
        async def _return_csv(self, data: List[Dict], metadata: Dict):
            """Return data as CSV format"""
            if not data:
                return {"error": "No data to convert to CSV", "success": False}
            
            try:
                import io
                import csv
                
                output = io.StringIO()
                
                # Get all unique keys from all records
                all_keys = set()
                for item in data:
                    all_keys.update(item.keys())
                
                fieldnames = sorted(list(all_keys))
                writer = csv.DictWriter(output, fieldnames=fieldnames)
                writer.writeheader()
                
                for item in data:
                    # Handle nested dictionaries by converting to strings
                    row = {}
                    for key in fieldnames:
                        value = item.get(key, '')
                        if isinstance(value, (dict, list)):
                            row[key] = str(value)
                        else:
                            row[key] = value
                    writer.writerow(row)
                
                csv_content = output.getvalue()
                output.close()
                
                return {
                    'data': csv_content,
                    'format': 'csv',
                    'metadata': metadata
                }
                
            except Exception as e:
                logger.error(f"Error converting to CSV: {str(e)}")
                return {
                    'data': data,
                    'format': 'json',
                    'metadata': metadata,
                    'csv_error': str(e)
                }
        
        @self.app.get("/")
        async def root():
            """Root endpoint with API information"""
            return {
                "message": "Intelligent Web Scraper API",
                "version": "1.0.0",
                "description": "AI-powered web scraping with natural language prompts",
                "endpoints": {
                    "POST /scrape": "Main scraping endpoint - provide a natural language prompt",
                    "GET /health": "Health check endpoint",
                    "GET /": "This information endpoint"
                },
                "example_usage": {
                    "prompt": "Get latest iPhone prices from Amazon and Flipkart",
                    "max_items": 50,
                    "include_images": False,
                    "output_format": "json"
                },
                "supported_content_types": [
                    "products/ecommerce",
                    "jobs/careers",
                    "news/articles",
                    "real_estate/properties",
                    "general_content"
                ],
                "status": "operational",
                "timestamp": datetime.now().isoformat()
            }
        
        @self.app.post("/scrape-advanced")
        async def scrape_advanced_endpoint(request: dict):
            """Advanced scraping endpoint with more control"""
            try:
                # Parse request with additional parameters
                prompt = request.get('prompt', '')
                max_items = min(request.get('max_items', 50), 100)  # Cap at 100
                include_images = request.get('include_images', False)
                include_links = request.get('include_links', True)
                output_format = request.get('output_format', 'json')
                retry_failed = request.get('retry_failed', True)
                user_id = request.get('user_id')  # For rate limiting
                
                if not prompt:
                    return {"error": "Prompt is required", "success": False}
                
                # Check rate limits if user_id provided
                if user_id:
                    from datetime import timedelta
                    today = datetime.now().date()
                    
                    # Count today's scrapes for this user (would use MongoDB in production)
                    # For now, we'll trust the frontend to manage this
                    pass
                
                # Parse prompt using intelligent parser
                parsed_data = IntelligentPromptParser.parse_comprehensive_prompt(prompt)
                
                # Update extraction requirements with advanced options
                parsed_data['extraction_requirements'].update({
                    'max_items': max_items,
                    'include_images': include_images,
                    'include_links': include_links,
                    'data_format': output_format,
                    'retry_failed': retry_failed
                })
                
                if not parsed_data['target_websites']:
                    return {
                        "error": "No valid websites found in prompt. Please specify websites to scrape.",
                        "success": False,
                        "suggestion": "Try: 'Get iPhone prices from amazon.com and flipkart.com'"
                    }
                
                start_time = datetime.now()
                
                # Initialize scraper and perform scraping
                async with StealthScraper() as scraper:
                    tasks = []
                    for website in parsed_data['target_websites']:
                        task = scraper.scrape_website(website, parsed_data['extraction_requirements'])
                        tasks.append(task)
                    
                    # Execute all scraping tasks
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Process and aggregate results
                all_data = []
                successful_websites = 0
                failed_websites = []
                
                for i, result in enumerate(results):
                    website_info = parsed_data['target_websites'][i]
                    
                    if isinstance(result, Exception):
                        failed_websites.append({
                            'url': website_info.url,
                            'domain': website_info.domain,
                            'error': str(result),
                            'error_type': type(result).__name__
                        })
                        logger.error(f"Failed to scrape {website_info.url}: {str(result)}")
                    elif result and len(result) > 0:
                        all_data.extend(result)
                        successful_websites += 1
                        logger.info(f"Successfully scraped {len(result)} items from {website_info.domain}")
                    else:
                        failed_websites.append({
                            'url': website_info.url,
                            'domain': website_info.domain,
                            'error': 'No data extracted - possible structure mismatch',
                            'error_type': 'NoDataError'
                        })
                
                end_time = datetime.now()
                scraping_time = (end_time - start_time).total_seconds()
                
                # Create comprehensive metadata
                metadata = {
                    'success': len(all_data) > 0,
                    'record_count': len(all_data),
                    'websites_scraped_successfully': successful_websites,
                    'total_websites_attempted': len(parsed_data['target_websites']),
                    'success_rate': f"{(successful_websites / len(parsed_data['target_websites']) * 100):.1f}%" if parsed_data['target_websites'] else "0%",
                    'failed_websites': failed_websites,
                    'scraping_time_seconds': round(scraping_time, 2),
                    'content_type_detected': parsed_data['content_type'].value,
                    'extraction_confidence': parsed_data['confidence_score'],
                    'scraped_at': datetime.now().isoformat(),
                    'prompt_analysis': {
                        'original_prompt': prompt,
                        'websites_identified': [w.domain for w in parsed_data['target_websites']],
                        'content_type': parsed_data['content_type'].value
                    }
                }
                
                # Return appropriate format
                if output_format.lower() == 'csv' and all_data:
                    return await self._return_csv(all_data, metadata)
                elif output_format.lower() == 'excel' and all_data:
                    return await self._return_excel(all_data, metadata)
                else:
                    return {
                        'success': metadata['success'],
                        'data': all_data,
                        'metadata': metadata
                    }
                    
            except Exception as e:
                logger.error(f"Error in advanced scrape endpoint: {str(e)}")
                return {
                    'error': f"Internal server error: {str(e)}",
                    'success': False,
                    'data': [],
                    'metadata': {
                        'success': False,
                        'record_count': 0,
                        'scraping_time_seconds': 0,
                        'error_details': str(e)
                    }
                }
        
        async def _return_excel(self, data: List[Dict], metadata: Dict):
            """Return data as Excel format"""
            try:
                import io
                import pandas as pd
                
                # Convert to DataFrame
                df = pd.DataFrame(data)
                
                # Create Excel file in memory
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, sheet_name='Scraped_Data', index=False)
                    
                    # Add metadata sheet
                    metadata_df = pd.DataFrame([metadata])
                    metadata_df.to_excel(writer, sheet_name='Metadata', index=False)
                
                excel_data = output.getvalue()
                output.close()
                
                # Return base64 encoded for JSON response
                import base64
                excel_b64 = base64.b64encode(excel_data).decode('utf-8')
                
                return {
                    'data': excel_b64,
                    'format': 'excel',
                    'filename': f"scraped_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    'metadata': metadata
                }
                
            except ImportError:
                logger.warning("pandas/openpyxl not available, falling back to CSV")
                return await self._return_csv(data, metadata)
            except Exception as e:
                logger.error(f"Error creating Excel file: {str(e)}")
                return {
                    'data': data,
                    'format': 'json',
                    'metadata': metadata,
                    'excel_error': str(e)
                }


# Initialize FastAPI application
app = WebScrapingAPI().app

# Add CORS middleware for frontend integration
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add request logging middleware
from fastapi import Request
import time

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # Log request
    logger.info(f"Request: {request.method} {request.url}")
    
    response = await call_next(request)
    
    # Log response
    process_time = time.time() - start_time
    logger.info(f"Response: {response.status_code} - {process_time:.2f}s")
    
    return response

# Production-ready error handlers
from fastapi import HTTPException
from fastapi.responses import JSONResponse

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "success": False,
            "timestamp": datetime.now().isoformat()
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "success": False,
            "timestamp": datetime.now().isoformat()
        }
    )

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Intelligent Web Scraper API starting up...")
    logger.info("✅ StealthScraper initialized")
    logger.info("✅ IntelligentPromptParser ready")
    logger.info("✅ All endpoints configured")
    logger.info("🌐 API is ready to accept requests")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("🛑 Intelligent Web Scraper API shutting down...")
    logger.info("✅ Cleanup completed")

# Main entry point for production deployment
if __name__ == "__main__":
    import uvicorn
    
    # Production configuration
    uvicorn.run(
        "main:api",
        host="0.0.0.0",
        port=8000,
        workers=1,  # Single worker for Playwright compatibility
        log_level="info",
        access_log=True,
        reload=False  # Set to True for development
    )