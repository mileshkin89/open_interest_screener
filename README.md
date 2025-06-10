# 📈 Open Interest Screener v1.0.0
A powerful tool for **monitoring Open Interest (OI) changes** on cryptocurrency futures using a Telegram bot.

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
* The list of monitored cryptocurrencies is updated daily
* The bot stores historical data for each symbol
* On signal trigger, it calculates how many similar signals occurred for that asset in the past 24 hours

### 💬 Each Alert Includes
* 📈 **OI growth** detected
* 💰 **Price and volume change** during the signal intervalма
* 🔁 **Signal frequency** for that asset in the last 24 hours

📲 All delivered in a clear and user-friendly format right in your **Telegram chat** 

### Limitations

* 🔹 Most exchange APIs provide OI data only for 5-minute intervals, so signals are generated at the close of each 5-minute candle
* 🔹 Each Telegram user can run only one active scanner with a specific configuration. To use multiple configurations simultaneously, use separate Telegram account
* 🕒 In this version, timestamps in alerts may be displayed in UTC (Coordinated Universal Time), rather than your local time zone.

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
git clone https://github.com/mileshkin89/smart_tg_bot.git
cd smart_tg_bot
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
* `docker-compose-prod.yml` - creates named volumes for logs and databases in local Linux storage.

* `docker-compose-dev.yml` - links container volumes and local project folders.

Choose what suits you best. And run it with the command:

```
docker-compose -f docker-compose-*.yml up --build
```
🚀 Your bot is now running inside a container!

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
poetry run python src/main.py
```
🚀 The application is now up and running locally!

---

## 🛠️ Usage Guide
    
Follow these steps to start working with the Telegram bot:

### 🔎 1. Find the Bot
Search for your bot in the Telegram app using the name you registered via @BotFather.

### 🚀 2. Start Screen

Click the **Start** button on the bot's welcome screen to enter the main menu.
    
![start](.assets/screenshots/start_app.jpg)
    


### 📋 Command Menu
The bot provides quick navigation through the following commands:

![commands_menu](.assets/screenshots/commands_menu.jpg)


🔘 `/start` Opens the main menu with:

* ⚙️ <b>Settings</b>

* 📊 <b>Exchanges</b>

* Allows instant launch with default parameters.

  ![cmd_start](.assets/screenshots/cmd_start.jpg)



⚙️ `/settings` 

* Adjust the analysis **timeframe** (e.g., 5m, 15m) and **open interest threshold** (%).

* Click a button to choose a parameter, then enter an integer and send the message.

* When done, press **Run screener** to start monitoring.

  ![cmd_settings](.assets/screenshots/cmd_settings.jpg)


🌐 `/exchanges` 

* Manage the list of **active exchanges** to monitor.

* 🟢 Green = enabled, 🔴 Red = disabled.

* Click on the exchange button to toggle its status. A notification will confirm success.

    ![cmd_exchanges](.assets/screenshots/cmd_exchanges.jpg)


### ▶️ Launching the Screener
Once configuration is complete, press Run screener.

* You'll receive a confirmation with selected settings and active exchanges.

* The bot will then begin scanning and sending alerts when matching signals appear.

  ![signals](.assets/screenshots/signals.jpg)


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
### 📄 License

This project is licensed under the MIT License. See the LICENSE file for details.

