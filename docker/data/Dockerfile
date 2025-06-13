FROM python:3.12-bookworm

ENV PYTHONDONTWRITEBYTECODE=1

ENV PYTHONUNBUFFERED=1

ENV VIRTUAL_ENV=/opt/venv

#RUN useradd -u 1444 -m catalog

RUN apt-get update && apt-get install -y \
    python3-dev \
    gcc \
    zlib1g-dev \
    tabix \
    rsync

RUN python -m venv $VIRTUAL_ENV

ENV PATH="$VIRTUAL_ENV/bin:$PATH"

#RUN chown -R catalog:catalog $VIRTUAL_ENV

RUN mkdir -p /data

#RUN chown -R catalog:catalog /data

RUN mkdir -p /usr/local/share/seqrepo

#RUN chown -R catalog:catalog /usr/local/share/seqrepo

COPY data/ /data/

COPY docker/data/entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh

WORKDIR /data

#USER catalog

RUN pip install --upgrade pip setuptools wheel

RUN pip install -r requirements.txt

RUN seqrepo pull -i 2024-12-20

ENTRYPOINT ["/entrypoint.sh"]
