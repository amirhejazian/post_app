def calculate_dynamic_limit(post_id):
    """
    Calculate dynamic limits based on historical trends.
    Example: Limit is calculated based on ratings in the last 7 days.
    """
    key = f"post:{post_id}:limits"
    limits = cache.get(key)

    if not limits:
        # Fetch ratings in the last 7 days
        one_week_ago = now() - timedelta(days=7)
        recent_ratings = PostRate.objects.filter(
            post_id=post_id, created_at__gte=one_week_ago
        )
        rating_counts = recent_ratings.values("rate").annotate(count=models.Count("id"))

        # Calculate limits dynamically (e.g., count * 2, with a minimum of 10)
        limits = {
            str(entry["rate"]): max(10, entry["count"] * 2) for entry in rating_counts
        }
        cache.set(key, limits, timeout=3600)  # Cache for 1 hour

    return limits


def is_rate_limited(post_id, rate):
    """
    Check if a rate is limited for the post.
    Uses Redis to store and check counts.
    """
    key = f"post:{post_id}:rate:{rate}"
    limit = calculate_dynamic_limit(post_id).get(
        str(rate), 10
    )  # Default limit of 10 if not defined

    # Increment the count for the current hour
    current_timeframe = now().strftime("%Y%m%d%H")  # e.g., 2024122815 (YYYYMMDDHH)
    redis_key = f"{key}:{current_timeframe}"

    count = redis_client.get(redis_key)
    if count and int(count) >= limit:
        return True

    # Increment the count in Redis with expiration (1-hour window)
    redis_client.incr(redis_key)
    redis_client.expire(redis_key, 3600)
    return False
