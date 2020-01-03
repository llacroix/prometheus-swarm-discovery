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

Label name            |  Label Value
----------------------|---------------------------------------------------------------
`prometheus.enable`   | by default false
`prometheus.port`     | by default 80
`prometheus.job`      | by default the name of the service
`prometheus.network`  | network to expose
`prometheus.labels.*` | Any label starting with this is feeded to the `file_sd_config`


New format (inspired by traefik)

Label name                               | Label Value
-----------------------------------------|----------------------------------------------------------------
`prometheus.enable`                      | true or false
`prometheus.targets.<job>.networks`      | networks to get ips from (optional if on one network) unused if host specified
`prometheus.targets.<job>.scheme`        | set `__scheme__` on the current target instance (optional)
`prometheus.targets.<job>.host`          | If present use this as target host instead of ips of current service
`prometheus.targets.<job>.port`          | port default to (optional) (default: 80)
`prometheus.targets.<job>.path`          | set `__metrics_path__` on the current target job (optional)
`prometheus.targets.<job>.labels.<key>`  | key/value of labels for the job (optional)

One docker service can be used to discover unrelated services
