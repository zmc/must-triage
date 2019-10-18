import json
import os
import re

import must_triage.fs as fs
import must_triage.inspectors as inspectors

from must_triage.inspectors.base import Inspector


class OCS(Inspector):
    async def inspect(self):
        self.interests = dict()
        jsons = fs.find(
            self.root,
            lambda p: re.match('.*--format_json(-pretty)?$', p)
        )
        inspectors.merge_interests(
            self.interests,
            await self.inspect_jsons(jsons),
        )
        return self.interests

    async def inspect_jsons(self, paths):
        if not paths:
            return dict()
        interests = dict()
        for path in self._progress_class("Reading OCS files").iter(paths):
            interests[path] = await self._inspect_json(path)
        return interests

    async def _inspect_json(self, path):
        result = list()
        if os.stat(path).st_size == 0:
            result.append("File is empty")
            return result
        with open(path) as fd:
            try:
                obj = json.load(fd)
            except json.decoder.JSONDecodeError:
                result.append("Failed to parse JSON content")
                return result
        if 'health_detail' in path:
            result.extend(self.unhealthy(obj))
        return result

    def unhealthy(self, obj):
        result = list()
        if obj['status'] != 'HEALTH_OK':
            result.append(obj)
        return result
