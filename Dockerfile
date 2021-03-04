FROM odoo:13.0

USER root

RUN set -x; \
        apt-get update \
        && apt-get install -y --no-install-recommends \
            git \ 
            vim \
            python3-setuptools
COPY requirements.txt /tmp/requirements.txt
RUN pip3 install --no-cache-dir --upgrade pip -r /tmp/requirements.txt

USER odoo
