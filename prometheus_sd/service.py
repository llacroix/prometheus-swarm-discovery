import asyncio
import aiodocker
from aiofile import AIOFile
import sys
import json
# import toml
import logging

from .utils import (
    convert_labels_to_config,
    extract_prometheus_labels,
    label_template,
)

logger = logging.getLogger(__name__)


# async def load_containers(config, prom_config, service, task):
#     # DEPRECATED
#     # TODO remove
#     docker = config.get_client()
#     container_id = task["Status"]["ContainerStatus"]["ContainerID"]
#     container = await docker.containers.get(container_id)
# 
#     networks = container._container["NetworkSettings"]["Networks"]
# 
#     if not network_label:
#         if len(networks.keys()) > 1:
#             continue
#         else:
#             network_label = list(networks.keys())[0]
# 
#     ip_address = networks[network_label]["IPAddress"]
# 
#     url = "%s:%s" % (ip_address, port_label)
# 
#     scrape_config = {
#         "labels": discovery_labels,
#         "targets": [url]
#     }
# 
#     return scrape_config


def filter_tasks(tasks):
    """Filter tasks that seems impossible to parse further"""
    for task in tasks:
        if "ContainerStatus" not in task["Status"]:
            # Task probably stopped while this was getting fetched
            continue
        yield task


def relabel_prometheus(job_config):
    """Get some prometheus configuration labels."""
    relabel = {
        'path': '__metrics_path__',
        'scheme': '__scheme__',
    }

    labels = {
        relabel[key]: value
        for key, value in job_config.items()
        if key in relabel.keys()
    }

    # parse __param_ parameters
    for param, value  in job_config.get('params', {}).items():
        labels['__param_%s' % (param,)] = value

    return labels


async def get_containers(config, tasks):
    docker = config.get_client()
    containers = []

    for task in tasks:
        container_id = task["Status"]["ContainerStatus"]["ContainerID"]
        container = await docker.containers.get(container_id)
        containers.append(container)

    return containers

def get_hosts(prom_config):
    hosts = prom_config.get('hosts', '')

    if hosts:
        return [
            host.strip()
            for host in hosts.split(',')
            if host.strip()
        ]
    else:
        return []

def get_targets(prom_config, containers):
    targets = []

    networks_name = False
    if prom_config.get('networks'):
        networks_name = prom_config.get('networks').split(',')

    port = prom_config.get('port', '80')

    def format_host(ip_address):
        return "%s:%s" % (ip_address, port)    

    for container in containers:
        networks = container._container["NetworkSettings"]["Networks"]

        if not networks_name:
            networks_name = networks.keys()

        for network in networks_name:
            if network not in networks:
                continue

            address = networks[network]["IPAddress"]

            targets.append(format_host(address))

    return targets


async def load_service_configs(config, service):
    """
    Load service configs

    A service config has the following format:

    prometheus.enable = true | false
    prometheus.jobs.<job>.port = "port" | null # default 80
    prometheus.jobs.<job>.path = "/metrics" | null # default /metrics
    prometheus.jobs.<job>.scheme = "http" | "https" | null # default "http"
    prometheus.jobs.<job>.hosts = "host1,host2,host3" | null | default ip of containers
    prometheus.jobs.<job>.params.<key> = "value" 
    prometheus.jobs.<job>.networks = "network1,network2,network3" # default all networks
    prometheus.jobs.<job>.labels.<key> = "value"
    """

    docker = config.get_client()

    labels = service["Spec"]["Labels"]

    enabled_label = labels.get("prometheus.enable")

    # Convert service labels to dict
    prom_labels = extract_prometheus_labels(labels)
    prom_config = convert_labels_to_config(extract_prometheus_labels(labels))
    prom_config = prom_config.get('prometheus')

    # skip if disabled when enabled by default or
    # skip when not enabled by default and not enabled
    if (
        (config.enabled_by_default and enabled_label == 'false') or
        (not config.enabled_by_default and not enabled_label == 'true')
    ):
        return []

    # TODO create tasks to load containers and gather 
    # valid results and ignore failed ones. It's possible that some
    # container can die quickly and won't be available during the 
    # second call it will prevent the service discovery from crashing
    # and having one container prevent the whole config to get built
    filters = {
        "desired-state": "running",
        "service": service["Spec"]["Name"],
    }
    tasks = await docker.tasks.list(filters=filters)
    containers = await get_containers(config, filter_tasks(tasks))

    # In practice each service can declare multiple scrape jobs 
    # by default it will uses the ip of the containers linked to
    # the service or use the host being defined on the job config
    # definition
    # 
    # This enable setting configuration for services not hosted in
    # docker and have some configuration inside docker labels instead
    # of manually editing files.
    jobs = []
    for job, job_config in prom_config.get('jobs', {}).items():
        scrape_config = {
            "labels": {
                "job": job
            }
        }

        # Get remapped labels like __scheme__ and __metrics_path__
        # could potentially handle params like __param_
        scrape_config.get('labels').update(relabel_prometheus(job_config))
        # Get all labels and apply to job labels
        scrape_config.get('labels').update(job_config.get('labels', {}))

        targets = (
            get_targets(job_config, containers)
            if not job_config.get('hosts')
            else get_hosts(job_config)
        )

        # If no target found check next job config
        if not targets:
            continue

        # In the meantime pack all hosts together
        scrape_config['targets'] = targets
        #  TODO get container/service specific labels
        # for target in targets:
        #     new_scrape = target.copy()
        #     new_scrape['labels'] = target['labels'].copy()
        #     new_scrape['targets'] = [target]

        jobs.append(scrape_config)

    return jobs


async def load_existing_services(config):
    """
    Rebuild all the services scrape configurations.
    """
    docker = config.get_client()

    # TODO make this part async by creating tasks for each service
    # instead and gather results instead of turning this into sync
    # code
    configs = [
        job_config
        for service in await docker.services.list()
        for job_config in await load_service_configs(config, service)
    ]

    return configs


async def save_configs(config, sd_configs):
    """
    Save a configuration based on fetched configs from docker
    """
    logger.info("Configuration updated in %s" % (config.options.out))

    async with AIOFile(config.options.out, "w") as afp:
        logger.debug(sd_configs)
        await afp.write(json.dumps(sd_configs))


async def listen_events(config):
    """
    Listen for events and recreate the config whenever a container start/stop
    """
    docker = config.get_client()
    subscriber = docker.events.subscribe()

    logger.info("Listening for docker events")
    try:
        states = ["start", "stop"]
        while True:
            event = await subscriber.get()

            if event["Type"] == "container" and event["status"] in states:
                configs = await load_existing_services(config)
                save_config_task = config.loop.create_task(save_configs(config, configs))
                done, pending = await asyncio.wait([save_config_task])
                logger.debug("Save config and event tasks completed")

    except Exception as exc:
        logger.error("Something wrong happened", exc)
        await config.deinit()
        raise


async def save_all_configs(config):
    """
    Get all services configs and save them.

    This is mainly important to initialize the scrape configurations
    when the service starts. Or from time to time to keep things in
    sync in case an event was missed.
    """
    configs = await load_existing_services(config)
    await save_configs(config, configs)


async def main_loop(config):
    """
    Main loop for service discovery.

    Infinite loop running 2 tasks.

    1. First task save the current configuration
    2. Wait for events and on each event, rewrite the configuration the
       same way 1 does.

    If for some reasons, all task are completed start again. This could
    happen if the event socket times out or for any other reason why step 1
    and step 2 completes with an exception

    In a perfect world, it should not loop more than 1 time.
    """
    logger.info("Entering main loop")

    reinit_count = 0
    loop = config.loop

    config.init()

    while True:
        if reinit_count > 0:
            logger.info("Reinit mainloop %d" % (reinit_count))

        save_config_task = loop.create_task(save_all_configs(config))
        read_events_task = loop.create_task(listen_events(config))

        done, pending = await asyncio.wait(
            [save_config_task, read_events_task]
        )

        reinit_count += 1

    await config.deinit()
