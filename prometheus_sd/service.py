import asyncio
import aiodocker
from aiofile import AIOFile
import re
import sys
import json
import logging

from .utils import (
    convert_labels_to_config,
    extract_prometheus_labels,
    label_template,
)

logger = logging.getLogger(__name__)

invalid_label_name_chars = "[^a-zA-Z0-9_]"
invalid_label_name_re = re.compile(invalid_label_name_chars)

META_PREFIX = '__meta_docker'
LABEL_TEMPLATE = '%s_%s_label_%s'

def sanitize_label(label):
    return re.sub(invalid_label_name_re, "_", label)

def format_label(label_type, key):
    return LABEL_TEMPLATE % (
        META_PREFIX,
        label_type,
        sanitize_label(key)
    )

class Target(object):
    def __init__(self):
        self.service = None
        self.task = None
        self.container = None

    def format_labels(self, label_type, labels):
        return {
            format_label(label_type, key): value
            for key, value in labels.items()
        }

    def get_container_labels(self):
        if not self.container:
            return {}

        labels = self.container._container['Config'].get('Labels', {})
        return self.format_labels('container', labels)

    def get_task_labels(self):
        if not self.task:
            return {}

        labels = self.task['Labels']
        labels = self.format_labels('task', labels)
        labels["%s_task_name"] = self.task['ID']

        return labels

    def get_service_labels(self):
        labels = self.service["Spec"]["Labels"]
        return self.format_labels('service', labels)

    def clone(self):
        target = Target()
        target.container = self.container
        target.task = self.task
        target.service = self.service
        return target
            

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


async def get_containers_as_target(config, tasks):
    docker = config.get_client()
    targets = []

    for task in tasks:
        container_id = task["Status"]["ContainerStatus"]["ContainerID"]
        container = await docker.containers.get(container_id)

        target = Target()
        target.container = container
        target.task = task

        targets.append(target)

    return targets

def get_hosts(prom_config, service):
    hosts = prom_config.get('hosts', '')

    if hosts:
        target = Target()
        target.service = service
        target.hosts = [
            host.strip()
            for host in hosts.split(',')
            if host.strip()
        ]
        return [target]
    else:
        return []

def get_targets(prom_config, target_objects):
    targets = []

    networks_name = False
    if prom_config.get('networks'):
        networks_name = prom_config.get('networks').split(',')

    port = prom_config.get('port', '80')

    def format_host(ip_address):
        return "%s:%s" % (ip_address, port)    

    for target in target_objects:
        container = target.container
        networks = container._container["NetworkSettings"]["Networks"]

        if not networks_name:
            networks_name = networks.keys()

        for network in networks_name:
            if network not in networks:
                continue

            address = networks[network]["IPAddress"]

            new_target = target.clone()
            new_target.hosts = [format_host(address)]

            targets.append(new_target)

    return targets

async def get_target_objects(config, service):
    docker = config.get_client()
    filters = {
        "desired-state": "running",
        "service": service["Spec"]["Name"],
    }
    tasks = await docker.tasks.list(filters=filters)
    targets = await get_containers_as_target(config, filter_tasks(tasks))
    for target in targets:
        target.service = service
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

    service_labels = service["Spec"]["Labels"]

    enabled_label = service_labels.get("prometheus.enable")

    # Convert service labels to dict
    prom_labels = extract_prometheus_labels(service_labels)
    prom_config = convert_labels_to_config(extract_prometheus_labels(service_labels))
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

    target_objects = await get_target_objects(config, service)
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
        job_labels = {
            sanitize_label(key): value
            for key, value in job_config.get('labels', {}).items()
        }
        scrape_config.get('labels').update(job_labels)

        targets = (
            get_targets(job_config, target_objects)
            if not job_config.get('hosts')
            else get_hosts(job_config, service)
        )

        # If no target found check next job config
        if not targets:
            continue

        # In the meantime pack all hosts together
        # scrape_config['targets'] = targets
        # jobs.append(scrape_config)
        #  TODO get container/service specific labels
        for target in targets:
            new_scrape = scrape_config.copy()
            new_scrape['labels'] = scrape_config['labels'].copy()
            new_scrape['targets'] = target.hosts

            # Load meta labels from container,task,service 
            if config.options.use_meta_labels:
                if config.options.service_labels:
                    new_scrape['labels'].update(target.get_service_labels())
                if config.options.task_labels:
                    new_scrape['labels'].update(target.get_task_labels())
                if config.options.container_labels:
                    new_scrape['labels'].update(target.get_container_labels())

            jobs.append(new_scrape)

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
