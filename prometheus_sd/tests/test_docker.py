# -*- coding: utf-8 -*-
import pytest
import aiodocker
import os
import tarfile
import asyncio

from prometheus_sd.service import (
    load_service_configs,
    load_existing_services
)
from prometheus_sd.config import Config, get_parser


async def create_container(docker, image_name, pull=True):
    if pull:
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


async def create_service(docker, image_name, pull=True):
    if pull:
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
    image_name = "containous/whoami:latest"
    container = await create_container(docker, image_name=image_name)
    containers = await get_containers(docker)
    assert len(containers) > 0
    await container.delete(force=True)
    await docker.close()


async def test_listing_containers_services(loop):
    docker = aiodocker.Docker()
    await docker.swarm.init()
    image_name = "containous/whoami:latest"
    #containers = await get_containers(docker)
    service = await create_service(docker, image_name=image_name)
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
            tag="promsd:latest",
            encoding="gzip",
        )

        assert image is not None


    image_name = 'promsd:latest'

    config = {
        'ContainerSpec': {
            'Image': image_name,
            'Args': ['--out', '/tmp/test.json'],
            'Mounts': [
                {
                    'Type': 'bind',
                    'Source': '/var/run/docker.sock',
                    'Target': '/var/run/docker.sock'
                }
            ]
        }
    }

    labels = {
        "prometheus.enable": "true",
        "prometheus.jobs.main.port": "9090",
    }

    service = await docker.services.create(
        task_template=config,
        name="promsd-service",
        labels=labels
    )


    parser = get_parser()
    config = Config(parser, args=['--out', '/tmp/services.json'])

    # Could be done in a better way like waiting for service to be up
    await asyncio.sleep(10)

    service_inspect = await docker.services.inspect(service['ID'])

    configs = await load_service_configs(config, service_inspect)

    assert configs is not None

    configs2 = await load_existing_services(config)

    assert len(configs) == len(configs2)

    services = await docker.services.list()
    assert len(services) > 0
    await docker.services.delete(service['ID'])

    await docker.swarm.leave(force=True)
    await docker.close()
