import yaml

import must_triage.fs as fs
import must_triage.inspectors as inspectors


class OCP:
    def __init__(self, root):
        self.root = root

    def inspect(self):
        self.interests = dict()
        yamls = fs.find(self.root, lambda p: fs.has_ext(p, ['.yaml', '.yml']))
        inspectors.merge_interests(self.interests, self.inspect_yamls(yamls))
        return self.interests

    def inspect_yamls(self, paths):
        interests = dict()
        for path in paths:
            interests[path] = list()
            with open(path) as fd:
                try:
                    obj = yaml.safe_load(fd)
                except (yaml.scanner.ScannerError, yaml.parser.ParserError):
                    interests[path].append("Failed to parse YAML content")
                    continue
            pods = list()
            if obj['kind'].lower() == 'pod':
                pods.append(obj)
            elif obj['kind'].lower() == 'podlist':
                pods.extend(filter(
                    lambda o: o['kind'].lower() == 'pod',
                    obj['items']
                ))
            interests[path].extend(map(self.pod_ready, pods))
        return interests

    def pod_ready(self, obj):
        result = list()
        status = obj['status']
        try:
            container_statuses = status['containerStatuses']
        except KeyError:
            return [dict(
                pod_name=obj['metadata']['name'],
                status=status,
                )]
        not_ready = filter(lambda cs: cs['ready'] is False, container_statuses)
        for cs in not_ready:
            ts = cs['state'].get('terminated', dict())
            if (ts.get('reason', '').lower() == 'completed' and
                    ts.get('exitCode') == 0):
                continue
            result.append(
                f"Container '{cs['name']}' in "
                f"pod '{obj['metadata']['name']}' is not ready")
        return result
