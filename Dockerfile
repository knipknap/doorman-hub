FROM tiangolo/uwsgi-nginx-flask-docker
COPY ./spiffhub /app
ADD requirements.txt /
ADD ./static /app/static

RUN apt-get update \
    && apt-get -y install software-properties-common \
    && pip install -r /requirements.txt \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
