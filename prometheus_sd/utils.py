# -*- coding: utf-8 -*-
label_template = "prometheus.labels."
labels_prefix = "prometheus."

def extract_prometheus_labels(labels):
    prometheus_labels = {
        key: value
        for key, value in labels.items()
        if key.startswith(labels_prefix)
    }
    return prometheus_labels


def dotted_setter(obj, key):
    parts = key.split('.')

    if parts[0] not in obj:
        obj[parts[0]] = {}

    if len(parts) > 2:
        return dotted_setter(obj[parts[0]], ".".join(parts[1:]))
    else:
        def setter(value):
            obj[parts[0]][parts[1]] = value
        return setter


def convert_labels_to_config(prometheus_labels):
    config = {}

    for label, value in prometheus_labels.items():
        dotted_setter(config, label)(value)

    return config
