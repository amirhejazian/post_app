from rest_framework.pagination import CursorPagination


class PostCursorPagination(CursorPagination):
    page_size = 100
    ordering = ("-pub_date", "-id")
