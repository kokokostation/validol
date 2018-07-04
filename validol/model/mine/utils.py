def remove_from_cache(session, request):
    key = session.cache.create_key(request)
    session.cache.delete(key)