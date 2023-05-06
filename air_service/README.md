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

BASE_DIR = Path(__file__).resolve().parent.parent
DEBUG = True


ALLOWED_HOSTS = ['127.0.0.1']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# STATIC_DIR = os.path.join(BASE_DIR, 'static')
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATICFILES_DIRS = []

# celery
REDIS_HOST = '127.0.0.1'
REDIS_PORT = '6379'
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
```bash 
sudo service redis-server start  
redis-cli
```

# Celery 
###Celery Worker run on Windows
Run in new terminal:
```bash
pip install eventlet  
celery -A djangoweatherreminder worker -l info -P eventlet
```

###Celery beat
Run in new terminal:
```bash
celery -A djangoweatherreminder beat -l info 
```

## Test 

To run tests from the localhost, type in the folder next to the file `manage.py`:  
```bash
python manage.py test flights.tests
```


## Test and Deploy

Use the built-in continuous integration in GitLab.

- [ ] [Get started with GitLab CI/CD](https://docs.gitlab.com/ee/ci/quick_start/index.html)
- [ ] [Analyze your code for known vulnerabilities with Static Application Security Testing(SAST)](https://docs.gitlab.com/ee/user/application_security/sast/)
- [ ] [Deploy to Kubernetes, Amazon EC2, or Amazon ECS using Auto Deploy](https://docs.gitlab.com/ee/topics/autodevops/requirements.html)
- [ ] [Use pull-based deployments for improved Kubernetes management](https://docs.gitlab.com/ee/user/clusters/agent/)
- [ ] [Set up protected environments](https://docs.gitlab.com/ee/ci/environments/protected_environments.html)

***

# Editing this README

When you're ready to make this README your own, just edit this file and use the handy template below (or feel free to structure it however you want - this is just a starting point!). Thank you to [makeareadme.com](https://www.makeareadme.com/) for this template.

## Suggestions for a good README
Every project is different, so consider which of these sections apply to yours. The sections used in the template are suggestions for most open source projects. Also keep in mind that while a README can be too long and detailed, too long is better than too short. If you think your README is too long, consider utilizing another form of documentation rather than cutting out information.

## Name
Choose a self-explaining name for your project.

## Description
Let people know what your project can do specifically. Provide context and add a link to any reference visitors might be unfamiliar with. A list of Features or a Background subsection can also be added here. If there are alternatives to your project, this is a good place to list differentiating factors.

## Badges
On some READMEs, you may see small images that convey metadata, such as whether or not all the tests are passing for the project. You can use Shields to add some to your README. Many services also have instructions for adding a badge.

## Visuals
Depending on what you are making, it can be a good idea to include screenshots or even a video (you'll frequently see GIFs rather than actual videos). Tools like ttygif can help, but check out Asciinema for a more sophisticated method.

## Installation
Within a particular ecosystem, there may be a common way of installing things, such as using Yarn, NuGet, or Homebrew. However, consider the possibility that whoever is reading your README is a novice and would like more guidance. Listing specific steps helps remove ambiguity and gets people to using your project as quickly as possible. If it only runs in a specific context like a particular programming language version or operating system or has dependencies that have to be installed manually, also add a Requirements subsection.

## Usage
Use examples liberally, and show the expected output if you can. It's helpful to have inline the smallest example of usage that you can demonstrate, while providing links to more sophisticated examples if they are too long to reasonably include in the README.

## Support
Tell people where they can go to for help. It can be any combination of an issue tracker, a chat room, an email address, etc.

## Roadmap
If you have ideas for releases in the future, it is a good idea to list them in the README.

## Contributing
State if you are open to contributions and what your requirements are for accepting them.

For people who want to make changes to your project, it's helpful to have some documentation on how to get started. Perhaps there is a script that they should run or some environment variables that they need to set. Make these steps explicit. These instructions could also be useful to your future self.

You can also document commands to lint the code or run tests. These steps help to ensure high code quality and reduce the likelihood that the changes inadvertently break something. Having instructions for running tests is especially helpful if it requires external setup, such as starting a Selenium server for testing in a browser.

## Authors and acknowledgment
Show your appreciation to those who have contributed to the project.

## License
For open source projects, say how it is licensed.

## Project status
If you have run out of energy or time for your project, put a note at the top of the README saying that development has slowed down or stopped completely. Someone may choose to fork your project or volunteer to step in as a maintainer or owner, allowing your project to keep going. You can also make an explicit request for maintainers.
