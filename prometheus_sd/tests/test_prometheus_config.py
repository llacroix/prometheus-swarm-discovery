# -*- coding: utf-8 -*-
import pytest

from prometheus_sd.service import relabel_prometheus


def test_config_relabel():
    job_config = {
        "path": "/metrics2",
        "scheme": "https",
        "params": {
            "par1": "1",
            "par2": "2",
            "par3": "3"
        },
        "labels": {
            "dummy1": "1",
            "dummy2": "2",
        }
    }

    prom_config = relabel_prometheus(job_config)

    assert prom_config.get('__metrics_path__') == '/metrics2'
    assert prom_config.get('__scheme__') == 'https'
    assert prom_config.get('__param_par1') == "1"
    assert prom_config.get('__param_par2') == "2"
    assert prom_config.get('__param_par3') == "3"

    assert len(prom_config.keys()) == 5
