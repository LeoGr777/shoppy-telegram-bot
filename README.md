# Shoppy – A collaborative shopping list bot for Telegram

<p align="center">
  <img src="https://upload.wikimedia.org/wikipedia/commons/8/82/Telegram_logo.svg" width="60" alt="Telegram Logo"/>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.11-blue" alt="Python 3.11"/>
  <img src="https://img.shields.io/badge/Telegram-Bot-blue?logo=telegram" alt="Telegram Bot"/>
  <img src="https://img.shields.io/badge/license-MIT-green" alt="MIT License"/>
</p>

Couples, flatmates, or families often manage shopping lists chaotically across scattered notes, messages, or different apps.  
Shoppy solves this problem directly **within Telegram**. It's simple, fast and accessible for everyone in the chat.
   
## Features
- Add items to a shared shopping list via simple commands.
- Mark items as purchased.
- Clear the entire list or keep specific items.
- Inline buttons for quick interaction.
- Works in private chats and groups.

## Installation

### 1. Local Development

```bash
git clone https://github.com/LeoGr777/shoppy-telegram-bot.git
cd <repo>
pip install -e .
cp .env.example .env  # Add your API_KEY
python main.py
```

### 2. Docker Deployment
```bash
docker build -t shoppy-telegram-bot:latest .
docker run -d --name shoppy-telegram-bot \
  --env-file .env \
  --restart unless-stopped \
  shoppy-telegram-bot:latest
```

## Project Structure
```bash
.
├── main.py                 # Bot entrypoint
├── database.py             # Database handling
├── pyproject.toml          # Python dependencies
├── Dockerfile              # Docker build instructions
├── .dockerignore
├── .gitignore
└── README.md
```

## Troubleshooting
- Error: API_KEY not found → Make sure .env exists and contains API_KEY=<your_token>.

- Docker build fails → Check Dockerfile and .dockerignore paths.

- Bot not responding in group → Add bot to group and grant message permissions.

## Contributing
Pull requests are welcome!
Please fork the repo and create a feature branch:

```bash
git checkout -b feature/your-feature
```

## License
MIT