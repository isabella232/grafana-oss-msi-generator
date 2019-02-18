FROM grafana/wix-toolset-ci:latest
USER root
RUN apt-get install -y \
    python3-venv python3-pip && \
    pip3 install -r ../generator/requirements.txt && \
    pip3 install Jinja2 MarkupSafe wget
USER xclient
