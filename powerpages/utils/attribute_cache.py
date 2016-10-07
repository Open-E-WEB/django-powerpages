# -*- coding: utf-8 -*-


def cache_result_on(attribute, as_property=False):
    """
    Decorator for methods whose value is cached on given attribute.
    `attribute` is a string template and method parameters can be used
    to render it.
    `as_property` can be used to convert method into property.
    """
    def _cache_result_on(method):
        def __cache_result_on(self, *args, **kwargs):
            cached_attr = attribute.format(*args, **kwargs)
            if not hasattr(self, cached_attr):
                setattr(self, cached_attr, method(self, *args, **kwargs))
            return getattr(self, cached_attr)
        if as_property:
            __cache_result_on = property(__cache_result_on)
        return __cache_result_on
    return _cache_result_on
