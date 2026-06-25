"""Response serializers — ORM instance to response-dict conversions.

Builders live here so that both controllers and services can reuse the same
serialization logic (the service cache-aside path serializes dicts to cache
without duplicating controller helpers).
"""
