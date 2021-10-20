# beng-lod-server


Works with Python >= 3.7

# prerequisites
Get yourself the lovely [pipenv](https://docs.pipenv.org/en/latest/)

From your command line run this from the repository root:
```
pipenv install
```
# create a settings file

Copy the settings-example.py to settings.py:

```
cp src/config/settings_example.py src/config/settings.py
```

Then change the settings to your liking...

# run the server
Using pipenv you can start the virtual environment and the server from the command line like this:
```
cd src
pipenv run python server.py
```

