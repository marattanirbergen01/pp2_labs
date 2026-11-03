import asyncio
import logging

from shopbot.app import run
from shopbot.config import load_config

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    asyncio.run(run(load_config()))
