# Shoppy – A collaborative shopping list bot for Telegram

<p align="center">
  <img src="https://upload.wikimedia.org/wikipedia/commons/8/82/Telegram_logo.svg" width="60" alt="Telegram Logo"/>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.13-blue" alt="Python 3.13"/>
  <img src="https://img.shields.io/badge/Telegram-Bot-blue?logo=telegram" alt="Telegram Bot"/>
  <img src="https://img.shields.io/badge/code%20style-ruff-D7FF64.svg" alt="Code style: ruff"/>
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

Requires [uv](https://docs.astral.sh/uv/). Use a separate test bot from BotFather, never the production token: two instances polling with the same token conflict (`409 Conflict`).

```bash
git clone https://github.com/LeoGr777/shoppy-telegram-bot.git
cd shoppy-telegram-bot
uv sync
uv run pytest && uv run ruff check
API_KEY=<test-token> DB_PATH=./data/dev.db uv run python -m shoppy
```

### Docker Deployment

Prerequisites: Docker with Compose and a `.env` file:

```
API_KEY=<your-telegram-bot-token>
```

```bash
mkdir -p data && sudo chown 1000:1000 data
docker compose up -d --build
```

Notes:
- The container runs as UID/GID 1000 (build args `APP_UID`, `APP_GID`), so `./data` must be writable by that user.
- The SQLite database (`DB_PATH`, default `/app/data/shopping_list.db`) also stores the ID of each chat's menu message, so the bot keeps editing the same message after a restart.
- Hardening in `compose.yaml`: read-only root filesystem, `cap_drop: [ALL]`, `no-new-privileges`.

## Project Structure
```
.
├── src/shoppy/
│   ├── __main__.py   # entry point (python -m shoppy)
│   ├── bot.py        # handlers, keyboards, application setup
│   ├── db.py         # SQLite access
│   └── parsing.py    # command and number parsing
├── tests/
├── pyproject.toml
├── uv.lock
├── Dockerfile
└── compose.yaml
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
- `API_KEY is not set` → Make sure `.env` exists and contains `API_KEY=<your_token>`.

- Bot not responding in group → Add bot to group and grant message permissions.

## Repository
The primary repository is hosted on a private Forgejo instance. This GitHub repository is a read-only mirror, so issues and pull requests are disabled.

## License
MIT