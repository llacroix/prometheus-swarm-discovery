[![Actions Status](https://github.com/llacroix/prometheus-swarm-discovery/workflows/Python%20application/badge.svg)](https://github.com/llacroix/prometheus-swarm-discovery/actions)
[![codecov](https://codecov.io/gh/llacroix/prometheus-swarm-discovery/branch/master/graph/badge.svg)](https://codecov.io/gh/llacroix/prometheus-swarm-discovery)
[![CII Best Practices](https://bestpractices.coreinfrastructure.org/projects/3629/badge)](https://bestpractices.coreinfrastructure.org/projects/3629)
[![Docker Pulls](https://img.shields.io/docker/pulls/llacroix/prometheus-swarm?style=plastic)](https://hub.docker.com/r/llacroix/prometheus-swarm)

Prometheus Docker Swarm Service Discovery
=========================================

This project has for goal to simplify service discovery for projects
hosted under docker swarm. By default, prometheus doesn't support docker
swarm and only propose as an alternative the `file_sd` service discovery.

More information about this here:

[file_sd_config](https://prometheus.io/docs/prometheus/latest/configuration/configuration/#file_sd_config)


How to use:
===========

Start the service on a host with docker swarm or as a docker swarm service by exposing the docker socket
to the service.

For example:

    docker run -it \
      -v /var/run/docker.sock:/var/run/docker.sock \
      -v prometheus.config:/config \
      llacroix/prometheus-swarm --out /config/file_sd.json

This would output the config file inside the `/config/file_sd.json` file and listen on the `/var/run/docker.sock`
by default. The volume named `prometheus.config` would be a volume used by prometheus or it could be a real mount
on the host if prometheus isn't running inside docker.


How to configure
================

Each prometheus service that needs to be exposed to prometheus must have a label `prometheus.enable` to `true`:

    prometheus.enable: true

Then you have to define `prometheus.port` if the port of the service is something else than `80`.

Other optional parameters are:

Format (inspired by traefik)

Label name                               | Label Value
-----------------------------------------|----------------------------------------------------------------
`prometheus.enable`                      | true or false
`prometheus.jobs.<job>.scheme`        | set `__scheme__` on the current target instance (optional)
`prometheus.jobs.<job>.hosts`         | If present use this as target host instead of ips of current service
`prometheus.jobs.<job>.port`          | port default to (optional) (default: 80)
`prometheus.jobs.<job>.path`          | set `__metrics_path__` on the current target job (optional)
`prometheus.jobs.<job>.params.<key>`  | key/value of params for the job (optional)
`prometheus.jobs.<job>.networks`      | networks to get ips from (optional if on one network) unused if host specified
`prometheus.jobs.<job>.labels.<key>`  | key/value of labels for the job (optional)

One docker service can be used to discover unrelated services 

TODO
====

- [x] Add metrics endpoint to allow prometheus to monitor the service itself
- [ ] Change architecture to allow swarm mode or base container mode
- [ ] Add tests / coverage to have an idea of the code quality
- [ ] Change architecture to allow other services than docker ones so it could support other platforms such as kubernetes,marathon...
- [ ] Add instruction to load labels from a resource type @service,@container etc.. The idea is to be able to load data generated by docker into labels

In order be able to support different kind of backend the intuition I have is that we have to keep it simple. Using docker as an example, 

We either have service or container as a main resource, if the service is the main resource, the targets are hosts/containers, if the main
resources are containers, then the targets are the hosts and the container. 

So a backend would have to define a Resource object and Targets

A Target would have sub-resources like itself, or a named one like a service or a container or a network... you name it. 

So our backend would have to be able to get resources, get targets from resources and have an Event Emitter that emits changes on either
a Target requiring changes. With a correctly set interface we can handle almost any kind of backend as long as they define the proper labels on
the resources/targets. To make it easier each Backend can create labels on the fly to adapt the schema to the unified prometheus labels configuration.

So as long as the format is similar, we can support many backends the same ways Traefik does through different plugins. So docker could be become
an optional backend if it's not used.

