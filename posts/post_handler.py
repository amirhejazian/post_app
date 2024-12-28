import json

from django.conf import settings

from posts.models import Post
from utils import redis_client

POST_CACHE_TTL = settings.POST_CACHE_TTL


def get_post_cache_key(post_id):
    return f"post_data:{post_id}"


def set_post_data_into_cache(post_id, post_data):
    cache_key = get_post_cache_key(post_id)
    redis_client.client.set(cache_key, json.dumps(post_data), ex=POST_CACHE_TTL)


def get_posts(post_ids):
    cache_keys = [get_post_cache_key(post_id) for post_id in post_ids]

    cached_data = redis_client.client.mget(cache_keys)

    missing_post_ids = []
    posts_data = {}

    for post_id, cached_value in zip(post_ids, cached_data):
        if cached_value is not None:
            posts_data[post_id] = json.loads(cached_value)
        else:
            missing_post_ids.append(post_id)

    if missing_post_ids:
        missing_posts = Post.objects.filter(id__in=missing_post_ids).values(
            "id", "title", "text"
        )

        for post_data in missing_posts:
            post_id = post_data.pop("id")
            posts_data[post_id] = post_data
            set_post_data_into_cache(post_id, post_data)

    return posts_data
