# Doorman home automation server

This repository contains a small home automation server that I installed
on a Raspberry PI.
It is written in Python/Flask and can easily be extended by putting new
drivers into app/drivers, which are just Python files with an
`on_init()` method.

## Warnings

The code for this server was pieced together from multiple sources in
a few hours, and includes numerous anti-patterns. Among other problems:

- It uses tons of plain (garbage) JS code instead of a proper UI framework
  like [Vue](https://vuejs.org/).

- It puts static files into the app folder and serves them through Flask
  without caching them in nginx.

- I am not planning to maintain it much. Pull requests and take-overs are welcome.

You have been warned.
That said, it should work as intended and most of these issues could probably
be fixed in a few hours, except for maybe the JS library part.

## Getting started

### Prerequisites

You need to have docker-compose installed.
Doorman has Docker images for amd64 and arm64.

### Installation

To force Docker to use the right platform version, make sure to run

```
docker pull knipknap/doorman-hub:latest --platform linux/amd64
```

or on ARM platforms:

```
docker pull knipknap/doorman-hub:latest --platform linux/arm64
```

To start Doorman, download the docker-compose.yml to your server,
and type `docker-compose up`.
