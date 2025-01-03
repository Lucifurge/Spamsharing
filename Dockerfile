FROM python:3.9-slim

# Install dependencies for headless Chrome
RUN apt-get update && \
    apt-get upgrade -y && \  # Upgrade all existing packages
    apt-get install -y \
    wget \
    curl \
    unzip \
    libxss1 \
    libappindicator3-1 \
    libindicator7 \
    libnss3 \
    libgdk-pixbuf2.0-0 \
    libatspi2.0-0 \
    libx11-xcb1 \
    libnss3-dev \
    libgbm-dev \
    chromium \
    --fix-missing && \  # Ensure any missing dependencies are fetched
    apt-get clean && \  # Clean up to reduce image size
    echo "Chromium and dependencies installed"

# Install Python dependencies
RUN pip install --upgrade pip
RUN pip install selenium flask flask-cors webdriver-manager

# Set environment variables for Chromium and ChromeDriver
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROME_DRIVER=/usr/local/bin/chromedriver

# Copy your Flask app
COPY . /app
WORKDIR /app

# Expose port
EXPOSE 5000

# Start the Flask app
CMD ["python", "app.py"]
