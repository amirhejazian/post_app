from rest_framework import serializers

from posts import rating_handler, post_handler
from posts.models import Post


class PostSerializer(serializers.Serializer):
    title = serializers.SerializerMethodField(method_name="get_title")
    text = serializers.SerializerMethodField(method_name="get_text")
    rate = serializers.SerializerMethodField(method_name="get_rate")
    rate_count = serializers.SerializerMethodField(method_name="get_rate_count")
    user_rate = serializers.SerializerMethodField(method_name="get_user_rate")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        queryset = args[0]
        post_ids = [post.id for post in queryset]
        self.posts_data = post_handler.get_posts(post_ids)
        self.posts_rating = rating_handler.get_posts_rating_data(post_ids)
        self.user_rates = None
        if user_id := kwargs["context"]["request"].user_id:
            self.user_rates = rating_handler.get_user_post_rates(post_ids, user_id)

    def get_title(self, obj):
        return self.posts_data[obj.id]["title"]

    def get_text(self, obj):
        return self.posts_data[obj.id]["text"]

    def get_rate(self, obj):
        return round(self.posts_rating[obj.id][0], 1)

    def get_rate_count(self, obj):
        return self.posts_rating[obj.id][1]

    def get_user_rate(self, obj):
        return self.user_rates and self.user_rates.get(obj.id)


class SubmitPostRateSerializer(serializers.Serializer):
    post_id = serializers.IntegerField(write_only=True)
    user_id = serializers.IntegerField(write_only=True)
    rate = serializers.IntegerField(min_value=0, max_value=5, write_only=True)

    def validate(self, attrs):
        validated_data = super().validate(attrs)
        if not Post.objects.filter(pk=validated_data["post_id"]).exists():
            raise serializers.ValidationError("Post does not exist")
        return validated_data

    def save(self):
        data = self.validated_data
        rating_handler.submit_rate(
            post_id=data["post_id"], user_id=data["user_id"], rate=data["rate"]
        )
