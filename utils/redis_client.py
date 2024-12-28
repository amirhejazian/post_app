from django.conf import settings
from redis import Redis

client = Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT)
