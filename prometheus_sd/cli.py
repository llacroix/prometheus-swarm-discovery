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


def main(args=None, watchdog_factory=None, loop=None):
    parser = get_parser()

    if loop is None:
        loop = asyncio.get_event_loop()

    config = Config(parser, args, loop)

    if not config.validate():
        return -1

    setup_logging(config)

    logger.info("Starting service")

    webserver = None
    if config.options.metrics:
        webserver = loop.create_task(make_server(config))
        config.tasks.add(('webserver', webserver))

    task = loop.create_task(main_loop(config))
    config.tasks.add(('discovery', task))

    await_tasks = config.get_tasks()

    if watchdog_factory:
        watchdog_task = loop.create_task(
            watchdog_factory(config)
        )
        await_tasks.append(watchdog_task)

    tasks = asyncio.wait(await_tasks)

    done, pending = loop.run_until_complete(tasks)

    logger.info("All tasks completed")

    return len(pending)
