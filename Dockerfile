FROM odoo:11.0

USER root

RUN set -x; \
        apt-get update \
        && apt-get install -y --no-install-recommends \
            git \ 
            vim \
            python3-setuptools

ARG addons=/mnt/extra-addons

COPY . ${addons}/

COPY requirements.txt ${addons}/requirements-innov-client.txt

RUN pip3 install --no-cache-dir --upgrade pip -r ${addons}/requirements-innov-client.txt
