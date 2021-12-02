# Doorman home automation server written in Python/Flask

This repository contains a small home automation server that I installed
on a Raspberry PI.
It is written in Python/Flask and can easily be extended by putting new
drivers into app/drivers, which are just Python files with an
on_init() method.

There are multiple options for deployment:

- Using Docker or Docker Compose.
- Using [Piku](https://github.com/piku/piku).
- Installing on your own uwsgi server.

## Warnings

The code for this server was pieced together from multiple sources in
a few hours, and includes numerous anti-patterns. Among other problems:

- It uses it's own SQL library when it should propably use something like
 [Peewee](https://github.com/coleifer/peewee) instead.

- It uses tons of plain (garbage) JS code instead of a proper UI framework
  like [Vue](https://vuejs.org/).

- It stores it's data in a Sqlite DB in the app folder, instead of using a
  proper DB container.

- It puts static files into the app folder and serves them through Flask
  without caching them in nginx.

- I am not planning to maintain it much. Pull requests and take-overs are welcome.

You have been warned.
That said, it works as intended and most of these issues could probably
be fixed in a few hours, except for maybe the DB library part.

## Getting started

I actually recommend that you fork this repository, as it allows you to

- Manage all input parameters (environment variables mentioned below)
  in Github Environments.

- Use Github's Actions to deploy whenever you make any change.
  This repository includes an auto-deployment workflow, see
  [deploy.yml](.github/workflows/deploy.yml).

If you don't want to do that, you can also just download the
docker-compose.yml file and deal with setting variables yourself.