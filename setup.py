# -*- coding: utf-8 -*-
import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

with open("requirements.txt", "r") as fh:
    requirements = fh.read()

setuptools.setup(
    name="prometheus_sd",
    version="0.0.1",
    author="Archeti",
    author_email="info@archeti.ca",
    description=(
        "Python Service to Discover docker swarm services "
        "form prometheus"
    ),
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/llacroix/prometheus-sd",
    packages=setuptools.find_packages(),
    install_requires=requirements,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    entry_points={
        "console_scripts": [
            "prometheus_sd = prometheus_sd.cli:main",
        ],
    },
    package_data={
        "prometheus_sd": [
            "data/**/*"
        ],
    }
)
