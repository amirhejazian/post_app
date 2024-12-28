from rest_framework import generics, status
from rest_framework.response import Response

from posts.models import Post
from posts.pagination import PostCursorPagination
from posts.serializers import SubmitPostRateSerializer, PostSerializer
from utils.permissions import IsAuthenticated


class PostsView(generics.ListAPIView):
    pagination_class = PostCursorPagination
    serializer_class = PostSerializer
    queryset = Post.objects.all().only("id")


class SubmitRateView(generics.GenericAPIView):
    serializer_class = SubmitPostRateSerializer
    authentication_required = True
    permission_classes = [IsAuthenticated]

    def post(self, request, post_id, *args, **kwargs):
        data = request.data
        data.update({"user_id": request.user_id, "post_id": post_id})
        serializer = self.serializer_class(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"message": "Submitted successfully"}, status=status.HTTP_201_CREATED
        )
