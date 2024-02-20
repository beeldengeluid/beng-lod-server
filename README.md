# beng-lod-server
Works with Python 3.11

## Prerequisites
Get yourself the lovely [poetry](https://poetry-project.org/)


## Setup

From your command line run this from the repository root:

```sh
poetry install
```

and adjust `config/config.yml` to your liking...

## Running the server
Using poetry you can start the virtual environment and the server from the command line like this:

```sh
cd src
poetry run python server.py
```

When the server is started correctly, you can checkout the OpenAPI specification from your browser:

`http://127.0.0.1:5309/swagger`, or you can get RDF directly, for example:

```sh
curl -L -H "Accept: application/ld+json" http://127.0.0.1:5309/id/program/2101608130117680531
```

By adding the data domain to your hosts.conf file you will be able to serve all items from your machine, as if it were the production server itself:
```
# reroute the domain for dev purposes
	127.0.0.1       data.beeldengeluid.nl
```
This is especially convenient when you want to click items from the lod-view HTML pages. One more thing you need to do for this is change the application port in your settings.py:
```yaml
APP_PORT: 80
```
