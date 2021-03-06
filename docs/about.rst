About prometheus-swarm-sd
#########################

This service expose docker swarm services in a json scrape configuration for prometheus.

In order to discover services, each services must contain a small amount of information
on how to scrape data from them.

The main idea behind this service discovery service is that each service should be self
aware. So when you create a service you should be able to tell what endpoint has the 
/metrics to be exposed and on which port. If it was possible we could also potentially
expose authentication methods so sevice could expose credentials.  But it's not possible
as of yet because prometheus simply doesn't allow this.

If you need to setup credentials, you'll have to do it directly in the scrape config
in prometheus.yml.

As a result of a few limitation, this project is only good for exposing labels and targets.
It can't do much more than that. 

As the basic way to configure scrape jobs is highly inspired by traefik, it's possible to
not only configure an actual service itself but other services than the one on which the 
configuration lays on.

Why would you want to expose multiple scrape endpoint on a single service?
==========================================================================

Not everything is made equal and sometimes, a docker service can have multiple endpoints
in it. So being limited to one scrape config per service may not fit everybody. So to keep
things general the `prometheus.jobs.<job_name>.*` is added to labels so one service can define:

.. code-block:: python

  prometheus.jobs.frontend.port = "8080"
  prometheus.jobs.backend.port = "9090"

And prometheus will correctly be able to parse both endpoints.

As a side effect, it's also possible to do this:

.. code-block:: python

  prometheus.jobs.extra.hosts = "example.com:80,test.example.com:80"

This will create 2 targets on the job extra pointing to example.com and test.example.com. 
The main advantage is that with this method, there's no need to reload or restart prometheus.

Changes will be seen by the discovery services to a service and once the service is created, it
will notify prometheus through file_sd which will reload its internal configuration. What it
means for you i that if you need to add an host to promtheus, you can do it from
docker-compose or anything used to manage your services. The labels can be added on any service
so you don't have to manually edit anything inside the prometheus container if you run it from
a container.
