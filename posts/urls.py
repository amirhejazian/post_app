from django.urls import path

from posts import views

urlpatterns = [
    path("", views.PostsView.as_view(), name="post-list"),
    path("/<int:post_id>/rate", views.SubmitRateView.as_view(), name="submit-rate"),
]
