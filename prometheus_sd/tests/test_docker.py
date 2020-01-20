# -*- coding: utf-8 -*-
import pytest
import aiodocker

async def create_container(docker):
    image_name = "containous/whoami:latest"
    image = await docker.images.pull(image_name)

    config = {
        "Image": image_name,
    }
    container = await docker.containers.create(
        config=config,
        name="test_container"
    )
    await container.start()
    return container

async def get_containers(docker):
    containers = await docker.containers.list()
    return containers

async def test_listing_containers(loop):
    docker = aiodocker.Docker()
    #containers = await get_containers(docker)
    container = await create_container(docker)
    containers = await get_containers(docker)
    assert len(containers) > 0
    await container.delete(force=True)
    await docker.close()
