# beng-lod-server


Works with Python >= 3.7

# prerequisites
Get yourself the lovely [pipenv](https://docs.pipenv.org/en/latest/)

From your command line run this from the repository root:

```sh
pipenv install
```

# Create a settings file

Copy the settings-example.py to settings.py:

```sh
cp src/config/settings_example.py src/config/settings.py
```

Then change the settings to your liking...

# Run the server
Using pipenv you can start the virtual environment and the server from the command line like this:

```sh
cd src
pipenv run python server.py
```

When the server is started correctly, you can checkout the OpenAPI specification from your browser: 

`http://127.0.0.1:5309/`, or you can get RDF directly, for example: 

```sh
curl -L -H "Accept: application/ld+json" http://127.0.0.1:5309/id/program/2101608130117680531
``` 

By adding the data domain to your hosts.conf file you will be able to serve all items from your machine, as if it were the production server itself:
```
# reroute the domain for dev purposes
	127.0.0.1       data.beeldengeluid.nl
```
This is especially convenient when you want to click items from the lod-view HTML pages.
