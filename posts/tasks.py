import logging

from celery import shared_task

from posts_app.celery import app  # noqa

logger = logging.getLogger(__name__)


@shared_task(
    name="calculate-new-rate",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 7, "countdown": 5},
)
def calculate_new_rate_task(post_id, old_rate, new_rate):
    from posts import rating_handler

    rating_handler.calculate_new_post_rate(post_id, old_rate, new_rate)


@shared_task(
    name="migrate-rates-into-db",
)
def migrate_rates_into_db():
    from posts import rating_handler

    rating_handler.migrate_rates_into_db()
