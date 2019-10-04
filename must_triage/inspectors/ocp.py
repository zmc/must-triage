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
        cstatuses = obj['status']['containerStatuses']
        readies = list(map(lambda s: s['ready'], cstatuses))
        for i in range(len(readies)):
            if readies[i] is not True:
                result.append(
                    f"Container '{cstatuses[i]['name']}' in "
                    f"pod '{obj['metadata']['name']}' is not ready")
        return result
