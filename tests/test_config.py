# -*- coding: utf-8 -*-
import pytest

from prometheus_sd.config import (
    Config,
    get_parser,
    docker_url
)


class DockerClientMock(object):
    def __init__(self, url):
        self.url = url


def test_config_no_args():
    parser = get_parser()
    args = []

    config = Config(parser, args, DockerClientMock)

    assert config.validate() == False

    config = Config(parser, ['--out', 'text.json'], DockerClientMock)

    assert config.validate() == True

    config.init()

    assert config.inited == True
    assert config.get_client().url == docker_url
