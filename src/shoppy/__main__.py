"""Entry point: python -m shoppy"""

import logging
import os
import sys

from shoppy.bot import build_application
from shoppy.db import Database

DEFAULT_DB_PATH = "/app/data/shopping_list.db"


def main() -> None:
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
    )
    # httpx logs every request URL at INFO, and those URLs contain the bot token.
    logging.getLogger("httpx").setLevel(logging.WARNING)

    token = os.getenv("API_KEY")
    if not token:
        sys.exit("API_KEY is not set")

    db = Database(os.getenv("DB_PATH", DEFAULT_DB_PATH))
    db.setup()

    logging.info("Starting bot...")
    build_application(token, db).run_polling()


if __name__ == "__main__":
    main()
