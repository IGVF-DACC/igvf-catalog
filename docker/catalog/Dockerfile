FROM python:3.11

ENV PYTHONDONTWRITEBYTECODE 1

ENV PYTHONBUFFERED 1

ENV VIRTUAL_ENV=/opt/venv

RUN wget -q https://download.arangodb.com/arangodb310/DEBIAN/Release.key -O- | apt-key add - && \
  echo 'deb https://download.arangodb.com/arangodb310/DEBIAN/ /' | tee /etc/apt/sources.list.d/arangodb.list && \
  apt update && \
  curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
  apt-get install -y apt-transport-https nodejs arangodb3-client libpq-dev

RUN python -m venv $VIRTUAL_ENV

ENV PATH="$VIRTUAL_ENV/bin:$PATH"

WORKDIR /app

COPY . .

RUN pip install -r data/requirements.txt && \
  npm install

EXPOSE 2023

ENTRYPOINT [""]
CMD sh entrypoint.sh
