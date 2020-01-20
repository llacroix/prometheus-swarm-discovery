# -*- coding: utf-8 -*-
import pytest

from prometheus_sd.utils import (
    extract_prometheus_labels,
    dotted_setter,
    convert_labels_to_config,
    labels_prefix,
    format_label
)

def f():
    raise Exception("test")


def test_something():
    with pytest.raises(Exception):
        f()

def test_good_labels():
    labels = {
        "a.b.c": 1,
        "a.b.c.d": 2,
        "prometheus.jobs.fun": 3,
        "prometheus.enable": 4
    }

    new_labels = extract_prometheus_labels(labels)

    assert len(new_labels) == 2

    for key in new_labels.keys():
        assert key.startswith(labels_prefix) == True

def test_multi_value():
    ctx = {}

    dotted_setter(ctx, 'a.b.c')(1)
    dotted_setter(ctx, 'a.b.d')(2)
    dotted_setter(ctx, 'a.c.c')(3)
    dotted_setter(ctx, 'a.c.f')(4)

    assert ctx.get('a', {}).get('b', {}).get('c') == 1
    assert ctx.get('a', {}).get('b', {}).get('d') == 2
    assert ctx.get('a', {}).get('c', {}).get('c') == 3
    assert ctx.get('a', {}).get('c', {}).get('f') == 4

def test_format_label():

    assert format_label('service', 'id') == "__meta_docker_service_label_id"
    assert format_label('container', 'image') == "__meta_docker_container_label_image"
    assert format_label('container', 'some key') == "__meta_docker_container_label_some_key"
    assert format_label('v', 'a.b.c') == "__meta_docker_v_label_a_b_c"
    assert format_label('v.v', 'a.b.c') == "__meta_docker_v_v_label_a_b_c"

    # Not particularly great to replace each invalid char by '_' but okay...
    assert format_label('сервис', 'имя') == "__meta_docker________label____"
