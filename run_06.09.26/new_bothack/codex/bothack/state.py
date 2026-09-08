"""Small persistent-map operations used by the native world model."""


def truth(value):
    return value is not None and value is not False


def assoc(mapping, **values):
    return (mapping or {}) | values


def get_in(mapping, keys, default=None):
    for key in keys:
        if mapping is None:
            return default
        try:
            mapping = mapping[key]
        except (KeyError, IndexError):
            return default
    return mapping


def assoc_in(mapping, keys, value):
    key, *rest = keys
    if isinstance(mapping, (list, tuple)):
        result = list(mapping)
        result[key] = assoc_in(result[key], rest, value) if rest else value
    else:
        result = dict(mapping or {})
        result[key] = assoc_in(result.get(key), rest, value) if rest else value
    return result


def update_in(mapping, keys, function, *args):
    return assoc_in(mapping, keys, function(get_in(mapping, keys), *args))


def dissoc(mapping, *keys):
    return {k: v for k, v in (mapping or {}).items() if k not in keys}
