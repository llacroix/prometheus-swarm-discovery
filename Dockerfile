from ubuntu:bionic

COPY requirements.txt /requirements.txt

RUN apt-get update \
    && apt-get install -y python3.6 python3-pip \
    && pip3 install -r /requirements.txt \
    && rm -rf /var/lib/apt/lists/*

COPY service.py /service.py

ENTRYPOINT ["/usr/bin/python3", "/service.py"]
CMD []
