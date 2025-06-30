# NSE Pre-Market Data Downloader

[![GitHub Workflow Status](https://github.com/echocmd/nse-pre-market-data/actions/workflows/run.yml/badge.svg)](https://github.com/echocmd/nse-pre-market-data/actions)

This simple project is a python script which automatically downloads pre-market data from National Stock Exchange (NSE) of India. It uses github actions to download the data on each trading day and saves it as csv. 


## Features

- **Automated Daily Downloads:** Fetches data every trading day.
- **Data Storage:** Saves the downloaded data into a CSV file, organized by date.
- **Holidays:** Skips the weekends and custom list of market holidays.
- **Notifications:** Integrated with [ntfy.sh](https://ntfy.sh) to send push notifications when the script fails.


## Getting Started

You can fork this repository and configure your own github actions or run manually on your local machine.

### Option 1: On local machine

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/echocmd/nse-pre-market-data.git
    cd YOUR_REPOSITORY
    ```

2.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure Holidays:**
    Open the `holidays.txt` file and update market holidays in `YYYY-MM-DD` format.

4.  **Handle Notifications:**
    The script will send a notification if it fails. You have two choices:
    *   **Enable Notifications:** Set an environment variable with your ntfy.sh topic name.
      ```bash
      # On Windows
      set NTFY_TOPIC=your_ntfy_topic

      # On Linux/macOS
      export NTFY_TOPIC=your_ntfy_topic
      ```
    *   **Disable Notifications:** Open `main.py` and comment out the `send_ntfy_notification(...)` lines in the `main()` function.

5.  **Run the Script:**
    ```bash
    python main.py
    ```
    On successful run, you will find the downloaded CSV file in the `Data/` folder.

### Option 2: On GitHub Actions

This is the easiest way to have the script run every day without any manual intervention.

1.  **Fork the Repository:**

2.  **Set Up Ntfy Secret (Recommended):**
    *   Go to your forked repository's **Settings** > **Secrets and variables** > **Actions**.
    *   Click **New repository secret**.
    *   For the **Name**, enter `NTFY_TOPIC`.
    *   For the **Secret**, enter your [ntfy.sh](https://ntfy.sh) topic name (e.g., `my-nse-bot-alerts-123`).
    *   If you do not want notifications, you can skip this step. The script will simply log a warning that the secret is not set.

### Configuring the Schedule

The script is scheduled to run automatically at **10:00 AM IST** on trading days.

To change this:
1.  Edit the file `.github/workflows/run.yml`.
2.  Find the `cron` line inside the `schedule` section.
3.  Update the time. **Remember that the time must be set in UTC.**

---
