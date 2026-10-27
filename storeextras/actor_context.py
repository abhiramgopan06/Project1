from contextvars import ContextVar

_current_actor = ContextVar('current_store_actor', default=None)


def get_current_actor():
    return _current_actor.get()


class StoreActorMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        token = _current_actor.set(getattr(request, 'user', None))
        try:
            return self.get_response(request)
        finally:
            _current_actor.reset(token)
