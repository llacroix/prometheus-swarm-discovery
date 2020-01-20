# -*- coding: utf-8 -*-
import pytest
import asyncio
from prometheus_sd.cli import main


async def test_main():
    loop, webserver, service_task = main(['--out', 'file.json'], block=False)

    assert webserver == None
    assert service_task != None

    await asyncio.sleep(0)

    service_task.cancel()


async def test_main_with_metrics():
    loop, webserver, service_task = main(['--out', 'file.json', '--metrics'], block=False)

    assert webserver != None
    assert service_task != None

    await asyncio.sleep(0)

    service_task.cancel()


async def test_main_invalid():
    ret = main(['--metrics'], block=False)

    assert ret == -1
