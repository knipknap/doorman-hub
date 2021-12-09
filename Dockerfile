FROM python:3.6-buster
ENV PYTHONUNBUFFERED 1

ADD requirements.txt /
RUN mkdir /app \
    && touch /app/__init__.py \
    && apt-get update \
    && apt-get -y install software-properties-common \
    && pip install -r /requirements.txt \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY ./doormanhub /app/doormanhub
RUN ln -s doormanhub/static static

CMD sh -c "gunicorn -w 4 -b 0.0.0.0:80 doormanhub:app"