import os


def has_ext(path, ext):
    if not isinstance(ext, list):
        ext = [ext]
    return path.split('.')[-1] in ext


def find(path, callback):
    if os.path.isfile(path) and callback(path):
        return [path]
    results = list()
    for root, dirs, files in os.walk(path):
        matches = list(filter(callback, files))
        if matches:
            matches = [os.path.join(root, s) for s in matches]
            results.extend(matches)
    return results
