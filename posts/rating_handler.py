import logging

from django.utils import timezone
from rest_framework.utils import json

from posts.models import PostRate, Post
from posts.tasks import calculate_new_rate_task
from rate_limiter.handler import RateLimiter
from utils import redis_client

POST_RATE_CACHE_KEY_FORMAT = "post_rate:{}"

logger = logging.getLogger(__name__)

rate_limiter = RateLimiter(redis_client.client, prefix="post_rating_rate_limiter")


def get_post_rate_cache_key(post_id):
    return POST_RATE_CACHE_KEY_FORMAT.format(post_id)


def set_post_ratings_into_cache(mapping):
    cache_mapping = {}
    for post_id, rating_data in mapping.items():
        cache_mapping[get_post_rate_cache_key(post_id)] = json.dumps(rating_data)
    redis_client.client.mset(cache_mapping)


@rate_limiter.limit(limit_args=["user_id"], max_limit=5, bucket_increase_rate=0)
@rate_limiter.limit(limit_args=["post_id"], min_limit=10, bucket_increase_rate=0.5)
def submit_rate(post_id, user_id, rate):
    old_rate = (
        PostRate.objects.filter(post_id=post_id, user_id=user_id)
        .values_list("rate", flat=True)
        .first()
    )
    if old_rate is None:  # means user has not submitted before
        PostRate.objects.create(post_id=post_id, user_id=user_id, rate=rate)
    else:
        PostRate.objects.filter(post_id=post_id, user_id=user_id).update(
            rate=rate, updated_at=timezone.now()
        )

    # delay a celery task with rate and old_rate
    calculate_new_rate_task.delay(post_id, old_rate, rate)


def get_posts_rating_data(post_ids):
    cache_keys = [get_post_rate_cache_key(post_id) for post_id in post_ids]

    cached_data = redis_client.client.mget(cache_keys)

    missing_post_ids = []
    post_ratings = {}

    for post_id, cached_value in zip(post_ids, cached_data):
        if cached_value is not None:
            post_ratings[post_id] = json.loads(cached_value)
        else:
            missing_post_ids.append(post_id)

    if missing_post_ids:
        missing_posts = Post.objects.filter(id__in=missing_post_ids).values_list(
            "id", "rate", "rate_count"
        )
        missing_ratings = {}
        for post_id, rate, rate_count in missing_posts:
            missing_ratings[post_id] = [rate, rate_count]
        set_post_ratings_into_cache(missing_ratings)
        post_ratings.update(missing_ratings)

    return post_ratings


def get_post_rating_data(post_id):
    return get_posts_rating_data([post_id])[post_id]


def get_user_post_rates(post_ids, user_id):
    rates = PostRate.objects.filter(post_id__in=post_ids, user_id=user_id).values(
        "post_id", "rate"
    )
    return {rate["post_id"]: rate["rate"] for rate in rates}


def calculate_new_post_rate(post_id, old_rate, new_rate):
    with redis_client.client.lock(
            f"posts_rating_lock_{post_id}", blocking_timeout=3, timeout=3
    ):
        rate, rate_count = get_post_rating_data(post_id)
        total_rate = rate * rate_count
        total_rate += int(new_rate)
        if old_rate is None:
            rate_count += 1
        else:
            total_rate -= int(old_rate)
        rate = total_rate / rate_count
        set_post_ratings_into_cache({post_id: [rate, rate_count]})


def migrate_rates_into_db():
    """
    Reads all post rates from Redis cache and updates the database.
    Ensures data consistency by using a database transaction.
    """
    with redis_client.client.lock("migrate_rates_into_db", blocking=False, timeout=10):
        post_rate_keys = redis_client.client.keys(
            POST_RATE_CACHE_KEY_FORMAT.format("*")
        )

        if not post_rate_keys:
            logger.info("No cached post rates found.")
            return

        rates = redis_client.client.mget(post_rate_keys)

        post_updates = []
        for key, cached_value in zip(post_rate_keys, rates):
            post_id = int(key.decode().split(":")[-1])
            rate_data = json.loads(cached_value)
            rate, rate_count = rate_data
            post_updates.append((post_id, rate, rate_count))

        # with transaction.atomic():
        for post_id, rate, rate_count in post_updates:
            Post.objects.filter(id=post_id).update(rate=rate, rate_count=rate_count)
