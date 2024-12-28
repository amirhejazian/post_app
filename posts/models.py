from django.db import models


class Post(models.Model):
    title = models.CharField(max_length=255)
    text = models.TextField()
    pub_date = models.DateTimeField(auto_now_add=True)
    rate_count = models.IntegerField(default=0)
    rate = models.FloatField(default=0)

    class Meta:
        indexes = [
            models.Index(fields=["pub_date", "id"]),
        ]

    def __str__(self):
        return self.title


class PostRate(models.Model):
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, null=False, blank=False, related_name="rates"
    )
    user_id = models.BigIntegerField(null=False, blank=False)
    rate = models.SmallIntegerField(null=False, blank=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["post", "user_id"], name="unique_user_post_rate"
            ),
        ]
