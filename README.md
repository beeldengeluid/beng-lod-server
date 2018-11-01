# beng-lod-server


Works with Python 2.7 and 3.x

# prerequisites
Install pip and then use it to install virtualenv:
```
pip install virtualenv
```

# virtual env
Install virtualenv (preferabbly with the name venv, so it's properly ignored by .gitignore; don't commit your virtualenv)
```
. venv/bin/activate
```

Then just use pip to install all the requirements: 

```
pip install -r requirements.txt
```
# create a settings file

copy the settings-example.py to settings.py

```
cp settings-example.py settings.py
```

Then change the settings to your liking

# run the server
```
cd src
python server.py
```
