from celery import Celery
import redis
import requests

cel = Celery(broker = 'redis://localhost/15', backend='redis://localhost/15')
redis_client = redis.Redis('localhost', db=13)

@cel.task(queue='http_queue', rate_limit="1/s")
def fetch_page(url):
    try:
        resp = requests.get('url')
        print resp
    except requests.HTTPError as e:
    	print 'Failed', e



@cel.task(queue='http_queue', rate_limit="1/s")
def fetch_pages():
	print 1




