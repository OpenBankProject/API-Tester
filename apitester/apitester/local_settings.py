SECRET_KEY = 'fafsdadsf'
# API hostname, e.g. https://api.openbankproject.com$
API_HOST = 'http://127.0.0.1:8080'
# Consumer key + secret to authenticate the _app_ against the API$
OAUTH_CONSUMER_KEY = '5eym4qlo2vw1thee5rv241mojkrmhoiujzfkhrhd'
OAUTH_CONSUMER_SECRET = 'kgd0h32v5ac2rb3ufwcspqxpcdxkwll2csxleb1a'
# Database filename, default is `../db.sqlite3` relative to this file$
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'apitester',
        'USER': 'apitester',
        'PASSWORD': 'apitester',
        'HOST': 'localhost',
        'PORT': '',
    }
}
