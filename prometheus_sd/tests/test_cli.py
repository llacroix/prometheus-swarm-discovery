# -*- coding: utf-8 -*-
import pytest
import asyncio
from prometheus_sd.cli import main


async def watchdog(config):
    await asyncio.sleep(1)
    config.shutdown.set_result(True)


async def test_main():

    ret = main(['--out', 'file.json'], watchdog_factory=watchdog)

    assert ret == 0


async def test_main_with_metrics():
    ret = main(['--out', 'file.json', '--metrics'], watchdog_factory=watchdog)

    assert ret == 0


async def test_main_invalid():
    ret = main(['--metrics'], watchdog_factory=watchdog)

    assert ret == -1


async def watchdog_kill(config):
    for task in config.tasks:
        task.cancel()
    config.shutdown.set_result(True)


async def test_watchdog_kill():
    ret = main(['--metrics'], watchdog_factory=watchdog_kill)
    assert ret == -1
