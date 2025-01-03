FROM python:3.9-slim

# Install dependencies for headless Chrome
RUN apt-get update && apt-get install -y \
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
    && apt-get clean \
    && echo "Chromium and dependencies installed"

# Install Python dependencies
RUN pip install --upgrade pip
RUN pip install selenium flask flask-cors webdriver-manager

# Set environment variables for Chromium and Chromedriver
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROME_DRIVER=/usr/bin/chromedriver

# Copy your Flask app
COPY . /app
WORKDIR /app

# Expose port
EXPOSE 5000

# Start the Flask app
CMD ["python", "app.py"]
