FROM python:3.11 AS base

ENV BRANCH docker

RUN wget -q https://download.arangodb.com/arangodb310/DEBIAN/Release.key -O- | apt-key add - && \
  echo 'deb https://download.arangodb.com/arangodb310/DEBIAN/ /' | tee /etc/apt/sources.list.d/arangodb.list && \
  apt update && \
  curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
  apt-get install -y apt-transport-https nodejs arangodb3-client libpq-dev

WORKDIR /scripts
COPY scripts .
RUN chmod -R +x /scripts

COPY . /app
WORKDIR /app
RUN chmod +x ./entrypoint.sh
RUN pip3 install -r data/requirements.txt && \
  npm install

ENTRYPOINT ["/app/entrypoint.sh"]
