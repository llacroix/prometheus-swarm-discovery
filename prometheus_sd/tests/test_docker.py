# -*- coding: utf-8 -*-
import pytest
import aiodocker


async def get_containers():
    docker = aiodocker.Docker()
    containers = await docker.containers.list()
    return containers

async def test_listing_containers(loop):
    containers = await get_containers()
    assert len(containers) > 0
