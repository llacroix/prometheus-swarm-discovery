# -*- coding: utf-8 -*-
import asyncio
import aiodocker
from aiofile import AIOFile
from optparse import OptionParser
import sys
import json
# import toml
import logging

from .config import Config
from .config import get_parser, setup_logging
from .service import main_loop

logger = logging.getLogger(__name__)

def main():
    parser = get_parser()
    config = Config(parser)

    if not config.validate():
        sys.exit(0)

    setup_logging(config)

    logger.info("Starting service")

    loop = asyncio.get_event_loop()
    config.loop = loop
    task = loop.create_task(main_loop(config))
    loop.run_until_complete(task)
    loop.close()

    logger.info("All tasks completed")
