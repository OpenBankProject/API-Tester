# API Tester

This is a Django project to test the Open Bank Project API from the outside.

To use this app, you need to authenticate against a sandbox where you have to have registered an account beforehand.


# Installation (development)

It is assumed that the git checkout resides inside a project directory, e.g. inside `/var/www/apitester` and thus to be found at `/var/www/apitester/API-Tester`.
Paths below are relative to this README. Files produced during installation or at runtime should be outside the git checkout, but inside the project directory, except for Django's local settings. 
The directory tree might look like:

```bash
$ tree -L 2 apitester/
apitester/
├── API-Tester
│   ├── apitester
│   ├── apitester.service
│   ├── gunicorn.conf.py
│   ├── LICENSE
│   ├── nginx.apitester.conf
│   ├── NOTICE
│   ├── README.md
│   ├── requirements.txt
├── logs
├── static-collected
│   ├── admin
│   ├── css
│   ├── img
│   ├── js
└── venv
    ├── bin
    └── lib
```

## Install dependencies

```bash
$ virtualenv --python=python3 ../venv
$ source ../venv/bin/activate
(venv)$ pip install -r requirements.txt
```

## Configure settings

Edit `apitester/apitester/local_settings.py`:

```python
# Used internally by Django, can be anything of your choice
SECRET_KEY = '<random string>'
# API hostname, e.g. https://api.openbankproject.com
API_HOST = '<hostname>'

# Consumer key + secret to authenticate the _app_ against the API
# When the app is created on the API, the redirect URL should point to this
# host + /obp, e.g. `http://localhost:8000/obp`
OAUTH_CONSUMER_KEY = '<key>'
OAUTH_CONSUMER_SECRET = '<secret>'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'dbname',
        'USER': 'dbuser',
        'PASSWORD': 'dbpassword',
        'HOST': 'localhost',
        'PORT': '',
    }
}
```

The application's authentication is API-driven. However, to make use of Django's authentication framework and sessions, there is a minimal requirement of a database. Per default, sqlite is used, but you can configure any Django-supported backend you want. Please lookup the appropriate documentation.


## Initialise database

```bash
(venv)$ ./apitester/manage.py migrate
```

## Run the app

```bash
(venv)$ ./apitester/manage.py runserver
```

The application should be available at `http://localhost:8000`.


# Installation (production)

Execute the same steps as for development, but do not run the app.

## Settings

Edit `apitester/apitester/local_settings.py` for _additional_ changes to the development settings above:

```python
# Disable debug
DEBUG = False
# Hosts allowed to access the app
ALLOWED_HOSTS = ['127.0.0.1', 'localhost', '<your public hostname here>']
# Directory to place static files in, defaults to `../static-collected` relative to this file
STATIC_ROOT = '<dirname>'
# Admins to send e.g. error emails to
ADMINS = [
        ('Admin', 'admin@example.com')
]
# Emails are sent from this address
SERVER_EMAIL = 'apitester@example.com'
# Emails are sent to this host
EMAIL_HOST = 'mail.example.com'
# Enable email security
EMAIL_TLS = True
```

## Static files

The app's static files, e.g. Javascript, CSS and images need to be collected and made available to a webserver. Run

```bash
(venv)$ ./apitester/manage.py collectstatic
```

The output will show where they are collected to (`settings.STATIC_ROOT`).

## Web application server

Instead of Django's built-in runserver, you need a proper web application server to run the app, e.g. `gunicorn`. It should have been installed already as a dependency and you can use the provided `gunicorn.conf.py`. Run it like

```bash
(venv)$ cd apitester/ && gunicorn --config ../gunicorn.conf.py apitester.wsgi 
```

- `gunicorn` does not start successfully when omitting the directory change and using `apitester.apitester.wsgi` as program.
- The user running  `gunicorn` needs to have write access to the _directory_ containing the database, as well as the database file itself.
- The app's output is logged to `gunicorn`'s error logfile (see `gunicorn.conf.py` for location)


## Process control

If you do not want to start the web application server manually, but automatically at boot and also want to restart automatically if it dies, a process control system comes in handy. This package provides configuration files for systemd and supervisor.

### systemd

Stick the provided file `apitester.service` into `/etc/systemd/system/`, edit to suit your installation and start the application (probably as root):

```bash
# /bin/systemctl start apitester
```

If it works properly, you might want it to be started at boot:

```bash
# /bin/systemctl enable apitester
```

If you need to edit the service file afterwards, it needs to be reloaded as well as the service
```bash
# /bin/systemctl daemon-reload
# /bin/systemctl restart apitester
```


### supervisor

Stick the provided file `supervisor.apitester.conf` into `/etc/supervisor/conf.d/`, edit to suit your installation and restart supervisor (probably as root):

```bash
# /bin/systemctl restart supervisor
```

## Webserver

Finally, use a webserver like `nginx` or `apache` as a frontend. It serves static files from the directory where `collectstatic` puts them and acts as a reverse proxy for gunicorn. Stick the provided `nginx.apitester.conf` into `/etc/nginx/sites-enabled/`, edit it and reload the webserver (probably as root):

```bash
# /bin/systemctl reload nginx
```


# Management

The app should tell you if your logged in user does not have the proper role to execute the management functionality you need. Please use a Super Admin user to login at an API Manager instance or API Explorer and set roles accordingly. To become Super Admin, set the property `super_admin_user_ids` in the API properties file accordingly.



# Final words

Be aware of file permission issues and preconfigured paths to executables (system env versus virtual env)!

Have fun,
 TESOBE
