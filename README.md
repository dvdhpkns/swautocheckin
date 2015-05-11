# SW Auto-Checkin

Automatically checkin to southwest flights 24 hours prior to flight time and get an A Group boarding pass. 

## Setup

Create a virtualenv

    virtualenv venv
    source venv/bin/activate

Install requirements

    pip install -r requirements.txt

Install redis

    brew install redis
    
Start redis

    # You can also configure launchd to start redis on login
    redis-server /usr/local/etc/redis.conf 
    
Sync DB

    ./manage.py migrate 
    
Add local host to sites

    python manage.py shell
    
    # add a new site to sites - the ID of this should match the SITES value in settings
    from django.contrib.sites.models import Site
    new_site = Site.objects.create(domain='localhost:8000', name='localhost')

## Running

Run the Django server

	./manage.py runserver
	
Start Celery

    celery -A swautocheckin.tasks worker --loglevel=info
	
### Running with Foreman

Alternatively, you can start both the server and Celery using foreman

    foreman start -p 8000
    