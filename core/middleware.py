from loguru import logger


class LogRequest:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if response.status_code >= 400:
            logger.warning(
                "Bad Request: User: {} ... {} {} with status code {}, {}",
                request.user.id if not request.user.is_anonymous else "Anonymous",
                request.method,
                request.path,
                response.status_code,
                response.content,
            )

        return response


class UpdateLastLoginMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        from django.contrib.auth.models import update_last_login

        response = self.get_response(request)

        if request.user.is_authenticated:
            update_last_login(None, request.user)

        return response
