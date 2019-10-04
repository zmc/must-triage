from . import ocp, ocs


def merge_interests(existing, new):
    for key, value in new.items():
        if value == []:
            continue
        if type(value) == list:
            value = filter(lambda v: v, value)
        if key not in existing:
            existing[key] = list()
        existing[key].extend(value)
    return existing


def all():
    return [ocp.OCP, ocs.OCS]
