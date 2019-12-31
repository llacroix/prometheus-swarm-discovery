import asyncio
import aiodocker
from aiofile import AIOFile
from optparse import OptionParser
import sys
import json

import logging

logger = logging.getLogger(__name__)

docker_url='unix:///var/run/docker.sock'

label_template = 'prometheus.labels.'

async def load_existing_services(docker):
    services = await docker.services.list()

    configs = []

    for service in services:
        labels = service["Spec"]["Labels"]

        enabled_label = labels.get('prometheus.enable')
        network_label = labels.get('prometheus.network')
        port_label = labels.get('prometheus.port', '80')
        job_label = labels.get('prometheus.job')
        
        discovery_labels = {
            "job": service['Spec']['Name'],
        }

        service_labels = {
            key.replace(label_template, ''): value
            for key, value in labels.items()
            if key.startswith(label_template)
        }

        discovery_labels.update(service_labels)

        filters = {
            "desired-state": "running",
            "service": service['Spec']['Name'],
        }

        if not enabled_label:
            continue

        tasks = await docker.tasks.list(filters=filters)

        for task in tasks:
            container_id = task['Status']['ContainerStatus']['ContainerID']
            container = await docker.containers.get(container_id)

            networks = container._container['NetworkSettings']['Networks']

            if not network_label:
                if len(networks.keys()) > 1:
                    continue
                else:
                    network_label = list(networks.keys())[0]

            ip_address = networks[network_label]['IPAddress']

            url = "%s:%s" % (ip_address, port_label)

            config = {
                "labels": discovery_labels,
                "targets": [url]
            }

            configs.append(config)

    return configs

async def save_configs(options):
    """
    Save a configuration based on fetched configs from docker
    """
    docker = aiodocker.Docker(url=options.host)
    configs = await load_existing_services(docker)

    logger.info("Configuration updated in %s" % (options.out))

    async with AIOFile(options.out, 'w') as afp:
        logger.debug(configs)
        await afp.write(json.dumps(configs))

    await docker.close()

async def listen_events(output):
    """
    Listen for events and recreate the config whenever a container start or stop
    """
    docker = aiodocker.Docker(url=options.host)
    subscriber = docker.events.subscribe()

    logger.info("Listening for docker events")

    while True:
        event = await subscriber.get()

        if (
            event['Type'] in ['container'] and
            event['status'] in ['start', 'stop']
        ):
            save_config_task = loop.create_task(save_configs(options))
            done, pending = await asyncio.wait([save_config_task])
            logger.debug("Save config and event tasks completed")

    await docker.close()

async def main_loop(options, args):
    """
    Main loop for service discovery.

    Infinite loop running 2 tasks.
    
    1. First task save the current configuration
    2. Wait for events and on each event, rewrite the configuration the same way 1 does.

    If for some reasons, all task are completed start again. This could happen if the event
    socket times out or for any other reason why step 1 and step 2 completes with an exception

    In a perfect world, it should not loop more than 1 time.
    """
    logger.info("Entering main loop")
    while True:
        save_config_task = loop.create_task(save_configs(options))
        read_events_task = loop.create_task(listen_events(options))

        done, pending = await asyncio.wait([save_config_task, read_events_task])

def setup_logging(options):
    level = logging.getLevelName(options.log_level)
    logger.setLevel(level)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    if not options.log_file:
        handler = logging.StreamHandler(sys.stdout)
    else:
        handler = logging.FileHandler(options.log_file)

    handler.setFormatter(formatter)
    logger.addHandler(handler)

if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option('-o', '--out', dest="out", help="Output File")
    parser.add_option('--host', dest="host", help="Docker Host/Socket", default=docker_url)
    parser.add_option('--log-level', dest='log_level', default='INFO')
    parser.add_option('--log-file', dest='log_file', default=None)

    (options, args) = parser.parse_args()

    setup_logging(options)

    if not options.out:
        parser.print_help()
        sys.exit(0)

    logger.info("Starting service")

    loop = asyncio.get_event_loop()
    task = loop.create_task(main_loop(options, args))
    loop.run_until_complete(task)
    loop.close()

    logger.info("All tasks completed")
