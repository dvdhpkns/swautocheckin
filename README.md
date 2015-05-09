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

    ./manage.py syncdb
    
Create log file

    

## Running

Run the Django server

	./manage.py runserver
	
Start Celery

    celery -A swautocheckin.tasks worker --loglevel=info
	
### Running with Foreman

Alternatively, you can start both the server and Celery using foreman

    foreman start -p 8000

