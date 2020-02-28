# -*- coding: utf-8 -*-
from aiohttp import web
from prometheus_client.metrics import Counter
from prometheus_client.registry import CollectorRegistry
from prometheus_client.exposition import choose_encoder
from prometheus_client.process_collector import ProcessCollector
from prometheus_client.gc_collector import GCCollector

from .metrics import (
    registry,
    req_counter
)

from aiohttp.web import AppRunner
from aiohttp.web import TCPSite

import logging

logger = logging.getLogger(__name__)

# TODO make the registry a context locals that is created by the config
# don't use a global value


async def metrics(request):
    """
    Metrics gathering route
    """
    req_counter.inc()
    accept_header = request.headers.get('Accept', '')
    encoder, content_type = choose_encoder(accept_header)
    output = encoder(registry)
    return web.Response(text=output.decode('utf-8'))


def make_app(config):
    """
    Create a small endpoint for metrics
    """
    app = web.Application()

    app.add_routes([
        web.get(config.options.metrics_path, metrics)
    ])

    return app


async def make_server(config):
    """
    Start a web server (aiohttp) using the web app
    """
    logger.info("Setting up web application")

    app = make_app(config)
    runner = AppRunner(app)

    logger.info("Setup")
    await runner.setup()

    site = TCPSite(
        runner,
        config.options.metrics_host,
        config.options.metrics_port
    )

    await site.start()

    logger.info("Metrics endpoint started on http://%s:%s%s" % (
        config.options.metrics_host,
        config.options.metrics_port,
        config.options.metrics_path
    ))

    await config.shutdown
