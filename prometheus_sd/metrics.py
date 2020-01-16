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
from prometheus_client.metrics import Counter, Histogram
from prometheus_client.registry import CollectorRegistry
from prometheus_client.process_collector import ProcessCollector
from prometheus_client.gc_collector import GCCollector

registry = CollectorRegistry()
process = ProcessCollector(registry=registry)
gc_collector = GCCollector(registry=registry)

req_counter = Counter('request_count', 'The amount of requests', registry=registry)
build_counter = Counter('build_count', 'The amount of time a config is saved', registry=registry)
event_counter = Counter('event_count', 'Amount of events received', registry=registry)

build_duration = Histogram('build_seconds', 'Time spent building config', registry=registry)
