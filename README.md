# AI Web Scraper

A powerful AI-driven web scraping tool built with Streamlit and Playwright, featuring user authentication, rate limiting, and admin controls.

## Features

- 🤖 AI-powered natural language scraping prompts
- 🔐 User authentication with MongoDB
- 📊 Data visualization and export (CSV/Excel)
- 🕷️ Stealth scraping with anti-detection
- 📱 Support for major e-commerce sites (Flipkart, Amazon)
- 🤖 robots.txt compliance checking

## Setup

### 1. Clone the repository
```bash
git clone <repository-url>
cd ai-web-scraper
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
playwright install chromium
```

### 3. Configure secrets
Create `.streamlit/secrets.toml` with your configuration:

```toml
# MongoDB Configuration
MONGODB_URI = "mongodb://localhost:27017/"

# Admin User Configuration
[admin]
username = "your_admin_username"
email = "admin@yourdomain.com"
password = "your_secure_admin_password"
```

### 4. Initialize admin user
```bash
python init_admin.py
```

### 5. Run the application
```bash
streamlit run app.py
```

## Usage

### For Regular Users
1. Register/Login to access the dashboard
2. Enter natural language scraping prompts
3. View results with interactive visualizations
4. Export data as CSV or Excel

### Example Prompts
- "Scrape top 50 mobiles from Flipkart with price, rating, and discount"
- "Get 30 laptops from Amazon with specifications and reviews"
- "Extract government notifications from ministry portal"
- "Scrape product data from e-commerce website https://example.com"


## File Structure
```
├── utils/
│   ├── auth_utils.py      # Authentication & user management
│   ├── scraper_utils.py   # Web scraping logic
│   └── robots_utils.py    # robots.txt compliance
├── Dashboard.py           # Main dashboard interface
├── init_admin.py         # Admin user initialization
├── .streamlit/
│   └── secrets.toml      # Configuration (not in git)
├── data/
│   └── scrape_log.json   # Rate limiting logs (not in git)
└── requirements.txt
```

## Security Features

- Password hashing with bcrypt
- Session-based authentication
- Rate limiting to prevent abuse
- robots.txt compliance checking
- Secrets management via Streamlit secrets
- MongoDB for secure data storage

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Ensure secrets are not committed
5. Submit a pull request

## License

This project is licensed under the MIT License.
