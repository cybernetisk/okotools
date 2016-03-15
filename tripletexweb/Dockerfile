FROM node:latest

RUN mkdir /home/henrik && \
    groupadd -g 500 henrik && \
    useradd -u 500 -g 500 henrik && \
    chown henrik:henrik /home/henrik

RUN apt-get update && \
    apt-get install -y vim && \
    rm -rf /var/lib/apt/lists/*

EXPOSE 3000

USER henrik
WORKDIR /opt
