web: gunicorn swautocheckin.wsgi --log-file -
worker: celery worker --app=swautocheckin.tasks.app