class AuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user_id = request.headers.get("X-User-Id")
        request.user_id = user_id
        response = self.get_response(request)
        return response
