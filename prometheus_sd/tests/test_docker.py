# -*- coding: utf-8 -*-
import pytest
import aiodocker
import os
import tarfile

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

async def create_service(docker):
    image_name = "containous/whoami:latest"
    image = await docker.images.pull(image_name)

    config = {
        'ContainerSpec': {
            'Image': image_name,
        }
    }

    service = await docker.services.create(
        task_template=config,
        name="test_service",
    )

    return service

async def test_listing_containers(loop):
    docker = aiodocker.Docker()
    #containers = await get_containers(docker)
    container = await create_container(docker)
    containers = await get_containers(docker)
    assert len(containers) > 0
    await container.delete(force=True)
    await docker.close()


async def test_listing_containers_services(loop):
    docker = aiodocker.Docker()
    await docker.swarm.init()
    #containers = await get_containers(docker)
    service = await create_service(docker)
    containers = await get_containers(docker)
    services = await docker.services.list()

    #assert len(containers) > 0
    assert len(services) > 0

    await docker.services.delete(service['ID'])
    await docker.swarm.leave(force=True)
    await docker.close()


async def test_build_image():
    docker = aiodocker.Docker()
    await docker.swarm.init()

    with tarfile.open('context.tar.gz', 'w:gz') as fout:
        for name in os.listdir('.'):
            fout.add(name)

    with open('context.tar.gz', 'rb') as context:
        image = await docker.images.build(
            fileobj=context,
            tag="promsd"
        )

        assert image is not None

    await docker.swarm.leave(force=True)
    await docker.close()
