# Django-Air-Service 



## Description
This project was developed as an imitation of a site for 
booking tickets for flights, as well as interaction with staff.
## Technologies used
`Python`,`Django`, `Celery`, `Websocket`, `Docker`, `PostgreSQL`, `Nginx`, `Bootstrap`, `Django-allauth`, `Stripe`, `Webpack`

## Getting started

To make it easy for you to get started with Django-Air-Service , 
here's a list of recommended next steps.

## Download
Download the repository with this command: 
```bash
git clone https://github.com/Shtierlitz/Django_Weather_Reminder.git ### переделать когда на гит отправлю
```
## Create Files
For the local server to work correctly, create your own file `local_settings.py` 
and place it in a folder next to the file `settings.py` of this Django project.
You will also need to create `.env` file and place it in the root of the project.

### Required contents of the local_settings.py file:
```python
import os
from pathlib import Path

from air_service.settings import USE_POSTGRES

BASE_DIR = Path(__file__).resolve().parent.parent


ALLOWED_HOSTS = ['localhost', '127.0.0.1']

if USE_POSTGRES:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': os.environ.get('DATABASE_NAME'),
            'USER': os.environ.get('DATABASE_USER'),
            'PASSWORD': os.environ.get('DATABASE_PASS'),
            'HOST': os.environ.get('DATABASE_HOST'),
            'PORT': '5432',
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# STATIC_DIR = os.path.join(BASE_DIR, 'static')
# STATICFILES_DIRS = []
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

# celery
REDIS_PORT = '6379'
if USE_POSTGRES:
    REDIS_HOST = '0.0.0.0'
    CELERY_BROKER_URL = f'redis://redis:{REDIS_PORT}/0'
    CELERY_RESULT_BACKEND = f'redis://redis:{REDIS_PORT}/0'
else:
    REDIS_HOST = '127.0.0.1'
    CELERY_BROKER_URL = f'redis://{REDIS_HOST}:{REDIS_PORT}/0'
    CELERY_RESULT_BACKEND = f'redis://{REDIS_HOST}:{REDIS_PORT}/0'
CELERY_BROKER_TRANSPORT_OPTIONS = {'visibility_timeout': 3600}
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'
CELERY_IMPORTS = [
    'flights.tasks',
]
# CELERY_RESULT_BACKEND = 'django-db'
CELERY_CACHE_BACKEND = 'django-cache'
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'my_cache_table',
    }
}
CELERY_RESULT_EXTENDED = True

```

### Required contents of the .env file:
```python
 
SECRET_KEY='<your SECRET key>'   

EMAIL_HOST_USER="<your email>"  
EMAIL_HOST_PASSWORD="<your google app password>"  
DEFAULT_FROM_EMAIL="<your email>"  
RECIPIENTS_EMAIL="<your email>"  

DATABASE_NAME="<database name>"  
DATABASE_USER="<database username>"  
DATABASE_PASS="<database password>"  
DATABASE_HOST="pg_db"  
DATABASE_PORT="5432"  

USER_PASS="<database user password>"

CLIENT_ID="<your SOCIALACCOUNT_PROVIDERS_google_app_client_id>"  

CLIENT_SECRET="<your SOCIALACCOUNT_PROVIDERS_google_app_secret>"  


STRIPE_SECRET="<your stripe_privat_secret_key>"
```

## Django run
To run localhost server just get to the folder where `manage.py` is and then run the command:
```bash
python manage.py runserver
```

## Redis cli run on Windows
Install Linux on Windows with WSL https://learn.microsoft.com/en-us/windows/wsl/install  
Install and run Redis cli https://redis.io/docs/getting-started/installation/install-redis-on-windows/  
Activate Ubuntu console and run:
```bash 
sudo service redis-server start  
redis-cli
```

# Celery  
### Celery Worker run on Windows
Run in new terminal:
```bash
pip install eventlet  
celery -A air_service worker -l info -P eventlet
```

### Celery beat
Run in new terminal:
```bash
celery -A air_service beat -l info 
```

## Test 

To run tests from the localhost, type in the folder next to the file `manage.py`:  
```bash
python manage.py test flights.tests
```

## Docker localhost
To use docker in localhost you need to have `local_settings.py` behind yours `settings.py` file.
```bash
run docker-compose -f docker-compose.yml up --build
````

## Docker localhost
To use docker in localhost you need to have `local_settings.py` behind yours `settings.py` file.
```bash
run docker-compose up --build
````

## Docker deploy
To use docker to deploy project on server you need to delete `local_settings.py`.  
Find server and create an instance.  
Run next commands:  
```bash
sudo apt-get update  
sudo apt-get install apt-transport-https ca-certificates curl gnupg-agent software-properties-common  
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -  
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"  
sudo apt-get update  
sudo apt-get install docker-ce  
sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)"  
sudo chmod +x /usr/local/bin/docker-compose  
docker --version  
```

### Now clone repository:
```bash
sudo git clone https://github.com/Shtierlitz/Django-Air-System.git
```
### Dont forget to create .env file
### Now you can run Docker container in your server machine:
```bash
sudo chmod +x entrypoint.prod.sh
sudo chmod +x init-letsencrypt.sh 
sudo ./init-letsencrypt.sh # creates a ssl certificate
sudo docker-compose -f docker-compose.prod.yml up -d --build
```
# Sources 
Celery https://docs.celeryq.dev/en/stable/getting-started/introduction.html  
Docker https://docs.docker.com/  
Redis https://redis.io/docs/getting-started/installation/install-redis-on-windows/  
DjangoSchool https://www.youtube.com/@DjangoSchool  
Websocket https://channels.readthedocs.io/en/latest/introduction.html  
Stripe https://stripe.com/docs  
Django-allauth https://django-allauth.readthedocs.io/en/latest/installation.html  
Render html to pdf https://www.youtube.com/watch?v=5umK8mwmpWM

