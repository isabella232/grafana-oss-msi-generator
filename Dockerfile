FROM grafana/wix-toolset-ci:latest
USER root
RUN apt-get install -y \
    python3-venv python3-pip && \
    pip3 install Jinja2 MarkupSafe wget && \
    curl -s https://packagecloud.io/install/repositories/github/git-lfs/script.deb.sh | sudo bash && \
    apt-get update && \
    apt-get install -y git-lfs && \
    git lfs install
COPY oss /master
RUN ls -l /master && \
    chmod a+rw /master
USER xclient
