# -*- coding: utf-8 -*-
import pytest
from prometheus_sd.service import (
    filter_tasks,
    get_hosts,
    Target
)


def test_get_hosts_empty():
    prom_config = {
    }
    service = {}

    hosts = get_hosts(prom_config, service)
    assert len(hosts) == 0

    prom_config = {
        'hosts': ''
    }

    hosts = get_hosts(prom_config, service)
    assert len(hosts) == 0


def test_get_hosts():
    prom_config = {
        'hosts': 'localhost:9090,127.0.0.1:8080,www.example.com'
    }
    service = {}

    hosts = get_hosts(prom_config, service)
    assert len(hosts) == 1
    assert 'localhost:9090' in hosts[0].hosts
    assert '127.0.0.1:8080' in hosts[0].hosts
    assert 'www.example.com' in hosts[0].hosts


def test_get_hosts2():
    prom_config = {
        'hosts': 'localhost:9090 , 127.0.0.1:8080 ,www.example.com  '
    }
    service = {}

    hosts = get_hosts(prom_config, service)
    assert len(hosts) == 1
    assert 'localhost:9090' in hosts[0].hosts
    assert '127.0.0.1:8080' in hosts[0].hosts
    assert 'www.example.com' in hosts[0].hosts


def test_filter_tasks():
    tasks = [
        {'id': 1},
        {'Status': {'ContainerStatus': {}}, 'id': 2},
        {'Status': {'ContainerStatus': {}}, 'id': 3},
        {'id': 4, 'Status': {}},
        {'Status': {'ContainerStatus': {}}, 'id': 5}
    ]

    filtered_tasks = [
        task
        for task in filter_tasks(tasks)
    ]

    assert len(filtered_tasks) == 3
    assert filtered_tasks[0]['id'] == 2
    assert filtered_tasks[1]['id'] == 3
    assert filtered_tasks[2]['id'] == 5


def test_empty_target():
    target = Target()

    c_labels = target.get_container_labels()
    assert isinstance(c_labels, dict)
    assert len(c_labels.keys()) == 0

    t_labels = target.get_task_labels()
    assert isinstance(t_labels, dict)
    assert len(t_labels.keys()) == 0

    s_labels = target.get_service_labels()
    assert isinstance(s_labels, dict)
    assert len(s_labels.keys()) == 0
