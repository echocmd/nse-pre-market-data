import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from time import sleep
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd
from curl_cffi.requests import Session, RequestsError

# --- Configuration ---
# URLs
PRE_MARKET_PAGE_URL = "https://www.nseindia.com/market-data/pre-open-market-cm-and-emerge-market"
DATA_DOWNLOAD_URL = "https://www.nseindia.com/api/market-data-pre-open?key=ALL"

# File Paths
LOG_FILE = "run.log"
HOLIDAY_FILE = "holidays.txt"
DATA_DIRECTORY = "Data"

# --- Logging Setup ---
def setup_logging():
    """Configures logging to both a rotating file and the console."""
    log_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S %Z'
    )
    
    # Rotating file handler
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=1_000_000,  # ~1 MB
        backupCount=3,
        encoding='utf-8'
    )
    file_handler.setFormatter(log_formatter)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_formatter)
    
    # Main logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

logger = setup_logging()

# --- Notification Function ---
def send_ntfy_notification(message, title="NSE Data Bot", priority="default"):
    ntfy_topic = os.getenv('NTFY_TOPIC')
    if not ntfy_topic:
        logger.warning("NTFY_TOPIC environment variable not set")
        return

    try:
        with Session() as s:
            s.post(
                f"https://ntfy.sh/{ntfy_topic}",
                data=message.encode('utf-8'),
                headers={"Title": title, "Priority": priority}
            )
        logger.info(f"Ntfy notification sent with priority '{priority}'")
    except RequestsError as e:
        logger.error(f"Failed to send ntfy notification: {e}")

# --- Core Logic Functions ---
def download_nse_data(max_retries=3, retry_delay=5):
    last_error = None
    for attempt in range(max_retries):
        try:
            logger.info(f"Attempt {attempt + 1}/{max_retries}: Starting pre-market data download")
            
            session = Session(impersonate="chrome120", timeout=20)

            logger.info("Fetching cookies from website...")
            session.get(PRE_MARKET_PAGE_URL)
            sleep(2)

            logger.info("Fetching Pre Market Data from NSE...")
            response = session.get(DATA_DOWNLOAD_URL)
            response.raise_for_status()

            data = response.json()

            # Validate the downloaded data
            if not isinstance(data, dict) or 'data' not in data or not isinstance(data['data'], list):
                raise ValueError("Invalid data format received from NSE")
            if not data['data']:
                raise ValueError("Empty data list received")

            logger.info("Successfully downloaded and validated NSE pre-market data!")
            return data

        except (RequestsError, ValueError) as e:
            last_error = e
            logger.warning(f"Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                delay = retry_delay * (2 ** attempt)
                logger.info(f"Retrying in {delay} seconds...")
                sleep(delay)

    logger.error(f"All {max_retries} download attempts failed. Last error: {last_error}", exc_info=last_error)
    return None

def save_to_csv(data, filename):
    try:
        os.makedirs(DATA_DIRECTORY, exist_ok=True)
        filepath = os.path.join(DATA_DIRECTORY, filename)

        stocks_data = data['data']
        df = pd.DataFrame(item['metadata'] for item in stocks_data)

        # filtered columns to save
        required_columns = [
            'symbol', 'identifier', 'previousClose', 'lastPrice', 'iep',
            'change', 'pChange', 'finalQuantity', 'totalTurnover', 'yearHigh', 'yearLow'
        ]
        
        # Filter the DataFrame to only include required columns
        filtered_df = df[[col for col in required_columns if col in df.columns]]

        filtered_df.to_csv(filepath, index=False)
        logger.info(f"Data successfully saved to {filepath}")
        return filepath

    except (IOError, KeyError, Exception) as e:
        logger.error(f"Failed to save data to CSV! Error: {e}", exc_info=e)
        return None

def is_trading_day():
    try:
        ist = ZoneInfo("Asia/Kolkata")
        today = datetime.now(ist)

        # Skip weekends (Sat,Sun)
        if today.weekday() >= 5:
            logger.info(f"Market is closed today (Weekend: {today.strftime('%A')})")
            return False

        # Check holidays list
        if os.path.exists(HOLIDAY_FILE):
            with open(HOLIDAY_FILE) as f:
                holidays = {line.strip() for line in f if line.strip()}
            if today.strftime("%Y-%m-%d") in holidays:
                logger.info(f"Market is closed today (Holiday: {today.strftime('%Y-%m-%d')})")
                return False
        else:
            logger.warning(f"{HOLIDAY_FILE} not found. Cannot check for holidays.")

        logger.info("Market is open today. Proceeding with download.")
        return True

    except Exception as e:
        logger.error(f"Error during trading day check: {e}", exc_info=e)
        # Fail-safe: Assume it's a trading day if the check fails
        return True

def main():
    logger.info("\n__________ NSE Data Downloader (v1.0) __________")

    if not is_trading_day():
        return

    data = download_nse_data()

    if data:
        today_str = datetime.now().strftime("%Y-%m-%d")
        filename = f"{today_str}.csv"
        saved_path = save_to_csv(data, filename)

        if not saved_path:
            send_ntfy_notification(
                "Critical error: Successfully downloaded NSE data but FAILED to save the CSV file.",
                "NSE Data - Save Error",
                priority="high"
            )
    else:
        send_ntfy_notification(
            "Critical error: FAILED to download pre-market data. NSE might be down or blocking requests.",
            "NSE Data - Download Failed",
            priority="high"
        )

if __name__ == "__main__":
    main()