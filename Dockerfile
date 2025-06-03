# Dockerfile

FROM python:3.11.8-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PLAYWRIGHT_BROWSERS_PATH=/opt/render/project/.cache/ms-playwright

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl wget gnupg ca-certificates fonts-liberation libappindicator3-1 libasound2 libatk-bridge2.0-0 libatk1.0-0 libcups2 libdbus-1-3 \
    libgdk-pixbuf2.0-0 libnspr4 libnss3 libx11-xcb1 libxcomposite1 libxdamage1 libxrandr2 xdg-utils libu2f-udev \
    libxss1 libxtst6 libgbm-dev libxshmfence1 libwayland-client0 libwayland-egl1 libxkbcommon0 libxext6 libxfixes3 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Install Playwright and its browsers
RUN pip install playwright && playwright install chromium --with-deps

# Copy project files
COPY . .

# Expose the port
EXPOSE 10000

# Run the app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
