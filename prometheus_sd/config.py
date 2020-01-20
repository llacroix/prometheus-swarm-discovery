# -*- coding: utf-8 -*-
##############################################################################
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import sys
import aiodocker
from optparse import OptionParser
import logging

logger = logging.getLogger(__name__)

docker_url = "unix:///var/run/docker.sock"

class Config(object):
    def __init__(self, parser, args=None, docker_client=aiodocker.Docker):
        self.parser = parser
        self.docker_client = docker_client

        self.call_args = args if args is not None else sys.argv[1:]

        (options, args) = parser.parse_args(self.call_args)

        self.options = options
        self.args = args
        self.inited = False
        self.enabled_by_default = not self.options.only_enabled

    def validate(self):
        if not self.options.out:
            self.parser.print_help()
            return False
        return True

    def init(self):
        self.docker = self.docker_client(url=self.options.host)
        self.inited = True

    async def deinit(self):
        await self.docker.close()
        self.inited = False

    def get_client(self):
        if not self.inited:
            self.init()
        return self.docker


def get_parser():
    parser = OptionParser()
    parser.add_option("-o", "--out", dest="out", help="Output File")
    parser.add_option(
        "--host", dest="host", default=docker_url, help="Docker Host/Socket",
    )
    parser.add_option("--log-level", dest="log_level", default="INFO")
    parser.add_option("--log-file", dest="log_file", default=None)
    parser.add_option("--only-enabled", dest="only_enabled", default=True)

    parser.add_option(
        "--meta-labels",
        action="store_true",
        dest="use_meta_labels",
        default=False
    )

    parser.add_option(
        "--service-labels",
        action="store_true",
        dest="service_labels",
        default=False
    )

    parser.add_option(
        "--container-labels",
        action="store_true",
        dest="container_labels",
        default=False
    )

    parser.add_option(
        "--task-labels",
        action="store_true",
        dest="task_labels",
        default=False
    )

    parser.add_option(
        '--metrics',
        action="store_true",
        dest="metrics",
        default=False
    )

    parser.add_option(
        '--metrics.path',
        dest="metrics_path",
        default="/metrics"
    )

    parser.add_option(
        '--metrics.port',
        dest="metrics_port",
        type="int",
        default=9090
    )

    parser.add_option(
        '--metrics.host',
        dest="metrics_host",
        default='localhost'
    )

    return parser


def setup_logging(config):
    options = config.options

    level = logging.getLevelName(options.log_level)
    logger = logging.getLogger('')
    logger.setLevel(level)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    if not options.log_file:
        handler = logging.StreamHandler(sys.stdout)
    else:
        handler = logging.FileHandler(options.log_file)

    handler.setFormatter(formatter)

    config.log_handler = handler

    logger.addHandler(handler)

    logger.info('Logging enabled')
