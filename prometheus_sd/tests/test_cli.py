# -*- coding: utf-8 -*-
import pytest
import asyncio
from prometheus_sd.cli import main


async def watchdog(config):
    await asyncio.sleep(1)
    config.shutdown.set_result(True)


def test_main():
    loop = asyncio.new_event_loop()

    ret = main(['--out', 'file.json'], watchdog_factory=watchdog, loop=loop)

    assert ret == 0


def test_main_with_metrics():
    loop = asyncio.new_event_loop()

    ret = main(['--out', 'file.json', '--metrics'], watchdog_factory=watchdog, loop=loop)

    assert ret == 0


def test_main_invalid():
    loop = asyncio.new_event_loop()

    ret = main(['--metrics'], watchdog_factory=watchdog, loop=loop)

    assert ret == -1


async def watchdog_kill(config):
    for task in config.tasks:
        task.cancel()

    config.shutdown.set_result(True)


def test_watchdog_kill():
    loop = asyncio.new_event_loop()

    ret = main(['--out', 'file.json', '--metrics'], watchdog_factory=watchdog_kill, loop=loop)

    assert ret == -1

def test_watchdog_kill_default_loop():
    ret = main(['--out', 'file.json', '--metrics'], watchdog_factory=watchdog_kill)

    assert ret == -1
