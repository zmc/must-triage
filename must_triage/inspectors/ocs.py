import json
import os
import re

import must_triage.fs as fs
import must_triage.inspectors as inspectors


class OCS:
    def __init__(self, root):
        self.root = root

    def inspect(self):
        self.interests = dict()
        jsons = fs.find(
            self.root,
            lambda p: re.match('.*--format_json(-pretty)?$', p)
        )
        inspectors.merge_interests(self.interests, self.inspect_jsons(jsons))
        return self.interests

    def inspect_jsons(self, paths):
        interests = dict()
        for path in paths:
            interests[path] = list()
            if os.stat(path).st_size == 0:
                interests[path].append("File is empty")
                continue
            with open(path) as fd:
                try:
                    obj = json.load(fd)
                except json.decoder.JSONDecodeError:
                    interests[path].append("Failed to parse JSON content")
                    continue
            if 'health_detail' in path:
                interests[path].extend(self.unhealthy(obj))
        return interests

    def unhealthy(self, obj):
        result = list()
        if obj['status'] != 'HEALTH_OK':
            result.append(obj)
        return result
