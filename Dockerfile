from ubuntu:disco

COPY . /prometheus_sd
#COPY requirements.txt /prometheus_sd/requirements.txt
#COPY prometheus_sd /prometheus_sd/prometheus_sd
#COPY setup.py /prometheus_sd/setup.py

RUN apt-get update \
    && apt-get install --no-install-recommends -y \
        python3 \
        python3-pip \
        python3-setuptools \
        python3-wheel \
    && cd /prometheus_sd \
    && pip3 install -U pip \
    && pip install -e . \
    #&& pip3 install -r /requirements.txt \
    && rm -rf /var/lib/apt/lists/*

#COPY service.py /service.py

ENTRYPOINT ["/usr/local/bin/prometheus_sd"]
CMD []
