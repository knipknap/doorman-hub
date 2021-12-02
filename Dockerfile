FROM tiangolo/uwsgi-nginx-flask:python3.9
ADD requirements.txt /

RUN touch /app/__init__.py \
    && apt-get update \
    && apt-get -y install software-properties-common \
    && pip install -r /requirements.txt \
    && rm -rf /var/lib/apt/lists/*

COPY ./app /app/app
COPY ./app/static /app/static
COPY ./app/uwsgi.ini /app