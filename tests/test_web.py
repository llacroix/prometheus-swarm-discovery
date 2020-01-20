# -*- coding: utf-8 -*-
import pytest
from prometheus_sd.server import (
    make_app,
    make_server
)
from prometheus_sd.config import Config, get_parser

async def test_app_metrics(aiohttp_client, loop):
    parser = get_parser()
    config = Config(parser)
    app = make_app(config)

    client = await aiohttp_client(app)

    resp = await client.get('/metrics')

    assert resp.status == 200

    text = await resp.text()
    lines = [
        line
        for line in text.split('\n')
        if not line.startswith('#')
    ]
    text = "\n".join(lines)

    assert len(lines) == 80

    assert 'promsd_request_count' in text
    assert 'promsd_build_count' in text
    assert 'promsd_event_count' in text
    assert 'promsd_reinit_count' in text
    assert 'promsd_errors_count' in text
    assert 'promsd_build_seconds' in text
    assert 'promsd_config_size_bytes' in text
    assert 'promsd_configs_units' in text
