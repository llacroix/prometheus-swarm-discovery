Configuration
#############


Basic Configuration to Run
==========================

This project is meant to be configured mostly through labels on the services you are running.
The configuration to run the service are quite minimal.

The only require configuration is the output file where to log the scrape configs. As prometheus
use file_sd, that's really the only required settings in a basic setup.

Running the service is as simple as this:

    prometheus_sd --out /path/to/config.json

Other settings can be found using the `--help` argument.

Configuring services
====================

Service configuration tries not to take things into account, as docker services aren't well
defined to exactly know what endpoint can be scraped. The labels are there to define that.

The configuration is quite similar to how it's done using the traefik proxy server.

Here's a list of currently supported features:

====================================  =======================================================
              Label                         Value
====================================  =======================================================
prometheus.enable                     true | false
prometheus.jobs.<job>.port            "port" | null # default 80
prometheus.jobs.<job>.path            "/metrics" | null # default /metrics
prometheus.jobs.<job>.scheme          "http" | "https" | null # default "http"
prometheus.jobs.<job>.hosts           "host1,host2,host3" | null | default ip of containers
prometheus.jobs.<job>.params.<key>    "value" 
prometheus.jobs.<job>.networks        "network1,network2,network3" # default all networks
prometheus.jobs.<job>.labels.<key>    "value"
====================================  =======================================================

If services are exposed by default then the minimum required would be to have at least one

`prometheus.jobs.<job>.<any>` attribute defined.

The minimal, albeit redundant, configuration would be this:

    prometheus.jobs.my_job.labels.job = "my_job"

It would expose the service configuration like the following:

.. code-block:: javascript

    [
        {
           "labels": {
              "job": "my_job",
              "__scheme__": "http",
              "__metrics_path__": "/metrics",
           },
           "targets": ["ip_instance:80"],
        }
    ]
 
If a service is in multiple networks, it will try to expose all the network ips unless requested otherwise.
Thought this behaviour could change in the future if you don't want the same service to be scraped from different
networks by default. 
