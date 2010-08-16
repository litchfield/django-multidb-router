import uuid
from django.conf import settings
from django.core.cache import cache

from .pinning import pin_this_thread, unpin_this_thread, this_thread_is_pinned


# The name of the cookie that directs a request's reads to the master DB
PINNING_COOKIE = getattr(settings, 'MULTIDB_PINNING_COOKIE', 'multidb_pin_writes')
PINNING_CACHE_PREFIX = getattr(settings, 'MULTIDB_PINNING_CACHE_PREFIX', 'multidb')

# The number of seconds for which reads are directed to the master DB after a
# write
PINNING_SECONDS = int(getattr(settings, 'MULTIDB_PINNING_SECONDS', 2)) #15))


class PinningRouterMiddleware(object):
    """Middleware to support the PinningMasterSlaveRouter"""
    def process_request(self, request):
        if cache.get(get_key(request)):
            pin_this_thread()
        else:
            # In case the last request this thread served was pinned:
            unpin_this_thread()

    def process_response(self, request, response):
        if this_thread_is_pinned():
            if PINNING_COOKIE not in request.COOKIES:
                response.set_cookie(PINNING_COOKIE, value=str(uuid.uuid1()))
            cache.set(get_key(request), True, PINNING_SECONDS)
        return response

def get_key(request):
    return PINNING_CACHE_PREFIX + str(hash('-'.join((request.META['REMOTE_ADDR'], 
                                                     request.META['HTTP_USER_AGENT'], 
                                                     request.COOKIES.get(PINNING_COOKIE, '')))))