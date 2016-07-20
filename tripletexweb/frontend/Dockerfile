FROM node:6
MAINTAINER Henrik Steen <henrist@henrist.net>

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

COPY app/package.json /usr/src/app/
RUN npm install

COPY app /usr/src/app

COPY container/build.sh /build.sh
COPY container/dev.sh /dev.sh
CMD ["/build.sh"]
