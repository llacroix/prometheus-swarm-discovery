# -*- coding: utf-8 -*-
import re

# Label names to look for
label_template = "prometheus.labels."
labels_prefix = "prometheus."

# META Labels support
META_PREFIX = '__meta_docker'
LABEL_TEMPLATE = '%s_%s_label_%s'

# Sanitize constants
invalid_label_name_chars = "[^a-zA-Z0-9_]"
invalid_label_name_re = re.compile(invalid_label_name_chars)

def extract_prometheus_labels(labels):
    prometheus_labels = {
        key: value
        for key, value in labels.items()
        if key.startswith(labels_prefix)
    }
    return prometheus_labels


def filter_key(key):
    new_key = key


    if key.startswith('"') and key.endswith('"'):
        new_key = new_key[1:-1]

    if not new_key.replace(' ', '').isalnum():
        raise Exception('Key can only be writable characters.')

    if new_key.replace(' ', '') == '':
        raise Exception('Empty key are not valid')

    return new_key


def dotted_setter(obj, key):
    parts = key.split('.')

    key1 = filter_key(parts[0])

    if key1 not in obj:
        obj[key1] = {}

    if len(parts) > 2:
        return dotted_setter(obj[key1], ".".join(parts[1:]))
    else:
        key2 = filter_key(parts[1])
        def setter(value):
            obj[key1][key2] = value
        return setter


def convert_labels_to_config(prometheus_labels):
    config = {}

    for label, value in prometheus_labels.items():
        dotted_setter(config, label)(value)

    return config


def sanitize_label(label):
    """Sanitize labels according to the recommendations"""
    return re.sub(invalid_label_name_re, "_", label)


def format_label(label_type, key):
    return LABEL_TEMPLATE % (
        META_PREFIX,
        label_type,
        sanitize_label(key)
    )
