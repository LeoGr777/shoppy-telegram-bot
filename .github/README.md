# Shoppy – A collaborative shopping list bot for Telegram

<p align="center">
  <img src="https://upload.wikimedia.org/wikipedia/commons/8/82/Telegram_logo.svg" width="60" alt="Telegram Logo"/>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.11-blue" alt="Python 3.11"/>
  <img src="https://img.shields.io/badge/Telegram-Bot-blue?logo=telegram" alt="Telegram Bot"/>
  <img src="https://img.shields.io/badge/code%20style-black-000000.svg" alt="Code style: black"/>
  <img src="https://img.shields.io/badge/license-MIT-green" alt="MIT License"/>
</p>

Couples, flatmates, or families often manage shopping lists chaotically across scattered notes, messages, or different apps.  
Shoppy solves this problem directly within Telegram. It's simple, fast and accessible for everyone in the chat.
   
## Features
- Add items to a shared shopping list via simple commands.
- Clear the entire list or keep specific items.
- Inline buttons for quick interaction.
- Works in private chats and groups.

### Example list:
![example_list_bot](https://i.postimg.cc/TYBsrhWC/photo-2025-09-04-18-48-11.jpg)

## Installation

### Local Development

```bash
git clone https://github.com/LeoGr777/shoppy-telegram-bot.git
cd <repo>
cp .env.example .env  # Add your API_KEY
```

### Docker Deployment

#### Prerequisites:

- A Telegram API token, see https://core.telegram.org/bots/api for details
- Docker & Docker Compose installed and running
- A .env file in the project root with at least:
    API_KEY=your-telegram-bot-token

#### Build & start:
```bash
docker compose up -d --build
```

#### Note:
- Docker will create a new user 'appuser' and grant ownership to the DIR to be able to write into the DB 
- The service binds ./app/data (host) to ./data (container). Your SQLite DB will appear on the host as .app/data/<shopping-list.db>.
- Security hardening is enabled in docker-compose.yaml (cap_drop: [ALL], security_opt: no-new-privileges:true).

## Project Structure
```bash
.
├── data/                   # persisted DB (bind mount)
│   └── shopping-list.db    
├── main.py                 # Bot entrypoint
├── pyproject.toml          
├── docker-compose.yaml     
├── dockerfile              
├── .dockerignore
├── .gitignore
└── README.md
```
## Usage within Telegram
- Within Telegram the bot can be searched via the chosen name
- Start a direct Chat or add the Bot to a group
- Available actions via buttons
  - Add item: Add an item via Keyboard. Multiple items can be added, separated by comma (e.g. bread, milk, rice)
  - Remove item: Remove an item by typing in the number(s separated with by comma)
  - Clear list: If this is chosen, a confirmation popup asks to 
    - Clear the complete list
    - Keep items: Type in items to keep separated by comma
    - Abort clearing process
- Available commands via Keyboard:
  - /start: Starts the bot
  - /add: Adds an item / multiple items
  - /done: Removes an item / multiple items via number(s)
  - /clearexcept: Clears the list except item number(s) 

### List of available commands:

![list_of_bot_commands](https://i.postimg.cc/Qx0hX82m/photo-2025-09-04-18-07-51.jpg)

### Starting Screen

![starting_screen_bot](https://i.postimg.cc/FFDmgFTS/photo-2025-09-04-18-07-49.jpg)

## Troubleshooting
- Error: API_KEY not found → Make sure .env exists and contains API_KEY=<your_token>.

- Docker build fails → Check Dockerfile and .dockerignore paths.

- Bot not responding in group → Add bot to group and grant message permissions.

## Contributing
Pull requests are welcome.
Please fork the repo and create a feature branch:

```bash
git checkout -b feature/your-feature
```

## License
MIT