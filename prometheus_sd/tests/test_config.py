# -*- coding: utf-8 -*-
import pytest
import logging

from prometheus_sd.config import (
    Config,
    get_parser,
    docker_url,
    setup_logging
)


class DockerClientMock(object):
    def __init__(self, url):
        self.url = url


def test_config_no_args():
    parser = get_parser()
    config = Config(parser, [], DockerClientMock)

    assert config.validate() == False


def test_config_minimal():
    parser = get_parser()
    config = Config(parser, ['--out', 'text.json'], DockerClientMock)

    assert config.validate() == True

    config.init()

    assert config.inited == True
    assert config.get_client().url == docker_url


def test_config_minimal_self_init():
    parser = get_parser()
    config = Config(parser, ['--out', 'text.json'], DockerClientMock)

    assert config.validate() == True
    assert config.get_client().url == docker_url
    assert config.inited == True


def test_config_metrics_config():
    parser = get_parser()

    args = [
        '--out', 'text.json',
        '--metrics',
        '--metrics.path', '/met',
        '--metrics.host', '0.0.0.0',
        '--metrics.port', '9191'
    ]

    config = Config(parser, args, DockerClientMock)
    config.init()

    assert config.options.metrics == True
    assert config.options.metrics_path == '/met'
    assert config.options.metrics_host == '0.0.0.0'
    assert config.options.metrics_port == 9191

    args = [
        '--out', 'text.json',
    ]

    config = Config(parser, args, DockerClientMock)
    config.init()

    assert config.options.metrics == False
    assert config.options.metrics_path == '/metrics'
    assert config.options.metrics_host == 'localhost'
    assert config.options.metrics_port == 9090


def test_config_log_level_base():
    parser = get_parser()
    args = [
        '--out', 'text.json',
    ]

    config = Config(parser, args, DockerClientMock)
    setup_logging(config)
    assert isinstance(config.log_handler, logging.StreamHandler)



def test_config_log_level_base_file():
    parser = get_parser()
    args = [
        '--out', 'text.json',
        '--log-file', 'out.log',
    ]

    config = Config(parser, args, DockerClientMock)
    setup_logging(config)
    assert isinstance(config.log_handler, logging.FileHandler)
