# 📈 Open Interest Screener v1.4.0
A powerful tool for **monitoring Open Interest (OI) changes** on cryptocurrency futures using a Telegram bot.

**You can use a real-time bot called** `@OI_futures_Screener_bot`

---
1. [**Overview**](#-overview)
2. [**Features**](#-features)
3. [**Installation**](#-installation)
4. [**Usage Guide**](#-usage-guide)
5. [**Project Structure**](#-project-structure)
6. [**Tech Stack**](#-tech-stack)
7. [**List of Versions**](#list-of-versions)
8. [**License**](#-license)

---
## 📝 Overview

**Open Interest Screener** analyzes real-time OI data from major crypto exchanges.
When a sharp increase in OI exceeds the configured threshold within a selected timeframe, the bot sends an instant **notification via Telegram**.

### 📌 What is Open Interest?
**Open Interest (OI)** represents the number of currently open futures contracts for a given asset.
A sudden increase in OI often indicates growing trader interest and fresh capital entering the market.

### 🔍 Why It Matters
Early detection of OI spikes helps traders:
* React quickly to potential price movements
* Make informed decisions before an asset gains mainstream attention

### 📅 Daily Crypto Monitoring
* The bot stores historical data for each symbol
* On signal trigger, it calculates how many similar signals occurred for that asset in the past 24 hours

### 💬 Each Alert Includes
* 📈 **OI growth** detected
* 💰 **Price and volume change** during the signal interval
* 🔁 **Signal frequency** for that asset in the last 24 hours
* 🌐 **Exchange name** is clickable — it links directly to the trading page of the asset on the corresponding exchange
* 🧾 **Symbol** is also clickable — for quick copy & paste into other tools or platforms

📲 All delivered in a clear and user-friendly format right in your **Telegram chat** 

### Limitations

* 🔹 Most exchange APIs provide OI data only for 5-minute intervals, so signals are generated at the close of each 5-minute candle
* 🔹 Each Telegram user can run only one active scanner with a specific configuration. To use multiple configurations simultaneously, use separate Telegram account

---
## 🚀 Features

### ⚙️ Flexible Configuration:
* Select analysis **timeframe**
* Set **open interest change threshold** (%)
* Choose **active exchanges** to monitor

🌐 **Multi-Exchange Support** - 
Supports multiple crypto exchanges such as Binance and Bybit

⚡ **High-Performance Architecture** - 
Fully asynchronous design for efficient real-time data processing

🤖 **Telegram Bot Integration** - 
Get instant alerts directly via a Telegram bot interface

💤 **Inactivity Auto-Shutdown** - 
Automatically disables scanners for inactive users to conserve system resources

---
## 📦 Installation

### 1. Clone the repository

```bash
git clone https://github.com/mileshkin89/open_interest_screener.git
cd open_interest_screener
```

### 2. Create and activate a virtual environment

<details>
<summary>Linux / macOS</summary>

```bash
python -m venv .venv
source .venv/bin/activate
```

</details>

<details>
<summary>Windows</summary>

```bash
python -m venv .venv
.venv\Scripts\activate
```

</details>


### 3. Create a .env file based on the template:

```bash
cp .env.sample .env
```

### 4. Add your Telegram Bot API token to .env

`TG_BOT_API_KEY=your_telegram_bot_token`

**Telegram Bot API Key**  
  Open [@BotFather](https://t.me/BotFather) in Telegram, use `/newbot`, and follow the prompts to create your bot and get the token.

###  Option 1: 🐳 Run with Docker
* `docker-compose-prod.yml` - creates named volumes for logs and databases in local Linux storage. Can be used to auto deploy using GitHub Actions

* `docker-compose-dev.yml` - links container volumes and local project folders. Recommended for running on a local machine

Choose what suits you best. Build and launch docker containers with the command:
```
docker-compose -f docker-compose-dev.yml up --build
```
🚀 Your bot is now running inside a container!

Run Docker Compose in detached mode:
```
docker-compose -f docker-compose-dev.yml up -d
```

View Logs:
```
docker-compose -f docker-compose-dev.yml logs
```

### Option 2: 💻 Run Locally (without Docker)

### 5. Create and activate a virtual environment with Poetry:

If you don’t have [Poetry](https://python-poetry.org/) installed, you can install it with:

```bash
pip install poetry
```

### 6. Install project dependencies:

```bash
poetry install
```

### 7. Run the bot:

```bash
cd src/
poetry run python main.py
```
🚀 The application is now up and running locally!

---

## 🛠️ Usage Guide
    
Follow these steps to start working with the Telegram bot:

### 🔎 1. Find the Bot
Search for your bot in the Telegram app using the name you registered via @BotFather.

### 🚀 2. Start Screen

Click the **Start** button on the bot's welcome screen to enter the main menu.

<img alt="start" height="580" src="assets/screenshots/start_app.jpg" width="300"/>
    


### 📋 Command Menu
The bot provides quick navigation through the following commands:

<img alt="commands_menu" height="580" src="assets/screenshots/commands_menu.jpg" width="300"/>


🔘 `/start` Opens the main menu with:

* ⚙️ <b>Settings</b>
* 📊 <b>Exchanges</b>
* Allows instant launch with default parameters.

  <img alt="cmd_start" height="580" src="assets/screenshots/cmd_start.jpg" width="300"/>


▶️ `/run` Instantly launches the screener with your current settings:

* Period, threshold, time zone, and selected exchanges are loaded from your preferences.
* Same as pressing the Run screener button in the menu.


🛑 `/stop` Stops the screener when it's not needed:
* Helps reduce notification spam and avoid unnecessary distractions.
* Helps reduce notification spam and avoid unnecessary distractions.
* Same as pressing the Stop scanner button in the menu.


⚙️ `/settings` 

* Adjust the analysis **timeframe** (e.g., 5m, 15m) and **open interest threshold** (%).
* Select your **time zone** to ensure signal timestamps are displayed correctly.
* When done, press **Run screener** to start monitoring.

  <img alt="cmd_settings" height="580" src="assets/screenshots/cmd_settings.jpg" width="300"/>


🌐 `/exchanges` 

* Manage the list of **active exchanges** to monitor.
* 🟢 Green = enabled, 🔴 Red = disabled.
* Click on the exchange button to toggle its status. A notification will confirm success.

  <img alt="cmd_exchanges" height="580" src="assets/screenshots/cmd_exchanges.jpg" width="300"/>


### ▶️ Launching the Screener
Once configuration is complete, press Run screener.

* You'll receive a confirmation with selected settings and active exchanges.

* The bot will then begin scanning and sending alerts when matching signals appear.

  <img alt="signals" height="580" src="assets/screenshots/signals.jpg" width="300"/>


### 💤 Inactivity Management
To save resources, the bot includes an auto-disable mechanism:

* If no button is pressed for several days, a confirmation message is sent.

* Press **Confirm** within 24 hours to continue scanning.

* If ignored, the screener stops and must be restarted manually.

---

## 📁 Project Structure
```
open_interest_screener/
├── .dockerignore                     # Defines files to exclude when building the Docker image.
├── .env.sample                       # Example of environment variables
├── .gitignore                        # Specifies which files to ignore in version control
├── Dockerfile                        # Instructions to build the Docker image.
├── docker-compose.yml                # Docker Compose configuration to run the services
├── README.md                         # Main project documentation.
├── poetry.lock                       # Dependency lock file generated by Poetry.
├── pyproject.toml                    # Project configuration
├── LICENSE                           # License file for open-source usage.
├── logs/
│   └── .gitkeep                      # Application log output
├── storage/
│   └──  signals.db                   # SQLite database
└── src/                              # Main application logic
    ├── __init__.py
    ├── main.py                       # The main entry point of the application.
    ├── config.py                     # Loads and stores configuration 
    ├── logging_config.py             # Configures logging format, levels, and file output.
    ├── app_logic/                    # Core business logic and scanning management.
    │   ├── __init__.py
    │   ├── condition_handler.py      # Evaluates whether an OI signal should be triggered.
    │   ├── default_settings.py       # Default values and constants.
    │   ├── user_activity.py          # Tracks user activity and determines inactivity.
    │   └── scanner/
    │       ├── __init__.py
    │       ├── scanner.py            # The logic for collecting and analyzing OI data
    │       └── scanner_manager.py    # Manages active scanners per user and symbol.
    ├── bot/                          # Implements the Telegram bot
    │   ├── __init__.py
    │   ├── bot_init.py               # Initializes the Telegram bot and dispatcher.
    │   ├── keyboards.py              # Generates inline keyboards for user interactions.
    │   ├── menu.py                   # Defines and builds the main menu layout.
    │   ├── msg_sender.py             # Handles sending messages and formatting output.
    │   ├── states.py                 # FSM states for user input and bot navigation.
    │   └── commands/                 
    │       ├── __init__.py
    │       ├── start.py              # Command handler for /start and welcome flow.
    │       ├── settings.py           # Commands for setting thresholds and timeframes.
    │       └── exchanges.py          # Commands to manage active exchanges per user.
    ├── db/                           # Database models
    │   ├── __init__.py
    │   ├── bot_users.py              # Model and queries for bot users and their preferences.
    │   └── hist_signal_db.py         # Stores and queries historical signal statistics
    └── exchange_listeners/           # API listeners data from crypto exchanges.
        ├── __init__.py
        ├── base_listener.py          # Abstract base class for exchange listeners.
        ├── binance_listener.py       # Listener for Binance Futures
        ├── bybit_listener.py         # Listener for Bybit Futures
        ├── exchange_urls.py          # URL templates and link generation logic for exchanges
        └── listener_manager.py       # Starts and stops listeners based on active user settings.
```

---

## 🧰 Tech Stack

This project is built using modern asynchronous Python tools and is designed for efficient real-time data processing and Telegram integration.

### 🧠 Core Libraries

* **aiogram** - 
A fully asynchronous and flexible framework for building Telegram bots with state management and advanced routing.

* **aiohttp** - 
Asynchronous HTTP client/server library used for non-blocking API requests to crypto exchanges.

* **aiosqlite** - 
Asynchronous wrapper around SQLite, allowing fast non-blocking interactions with the local database.

### ⚙️ Configuration & Environment

* **pydantic-settings** - 
Modern way to manage configuration via environment variables with validation and type annotations.

* **python-dotenv** - 
Loads variables from .env files into the environment during local development.

### 🗃️ Project Structure & Packaging

* **Poetry** - 
Dependency and packaging manager that simplifies project setup, virtual environments, and versioning.

### 🐳 Deployment & Containerization

* **Docker** - 
Provides consistent environment for running the bot in isolation, including dependencies and configurations.

* **docker-compose** -
Manages multi-container setup and simplifies running services like the bot with a single command.
---
## List of versions

**V1.1.0** 
* Implemented a button and a menu command to stop the screener
* Fixed the initial static exchange menu. The exchange menu now dynamically displays the currently active exchanges.

**V1.2.0**
* Implemented user local time detection in the /settings command. Signal notifications now correctly display the local time based on the user's time zone.

**V1.3.0**
* In signal messages, exchange names are now clickable — they open the trading page for the instrument on the corresponding exchange
* Symbols are now clickable — enabling quick copy-paste for use in external tools
* Added the /run command as a shortcut to start the screener — improves user navigation and overall UI flow

**V1.4.0**
* Extracted the symbol collection logic from the Scanner class into a standalone SymbolListHandler class
* SymbolListHandler runs as an independent background task and updates the list of tradable symbols once per minute

---
## 📄 License

This project is licensed under the MIT License. See the LICENSE file for details.

