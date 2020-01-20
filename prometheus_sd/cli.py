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
from .server import make_server

logger = logging.getLogger(__name__)

def main(args=None, block=True):
    parser = get_parser()
    config = Config(parser, args)

    if not config.validate():
        return -1

    setup_logging(config)

    logger.info("Starting service")

    loop = asyncio.get_event_loop()
    config.loop = loop

    webserver = None
    if config.options.metrics:
        webserver = loop.create_task(make_server(config))

    task = loop.create_task(main_loop(config))

    if block:
        loop.run_until_complete(task)
        loop.run_until_complete(webserver)
        logger.info("All tasks completed")
    else:
        return loop, webserver, task
