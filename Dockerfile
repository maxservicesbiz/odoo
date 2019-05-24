FROM odoo:11.0

USER root

RUN set -x; \
        apt-get update \
        && apt-get install -y --no-install-recommends \
            git \ 
            vim \
            python3-setuptools

# Install some deps python.

COPY requirements.txt requirements.txt

RUN pip3 install --no-cache-dir --upgrade pip -r requirements.txt

# Expose Odoo services
EXPOSE 8069 8071

# Set the default config file
ENV ODOO_RC /etc/odoo/odoo.conf

USER odoo

ENTRYPOINT ["/entrypoint.sh"]
CMD ["odoo"]