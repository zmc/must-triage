import json
import os
import re

from concurrent.futures import ProcessPoolExecutor

import must_triage.fs as fs
import must_triage.inspectors as inspectors

from must_triage.inspectors.base import Inspector
from must_triage.progress import ProgressBar


class OCS(Inspector):
    async def inspect(self):
        self.interests = dict()
        jsons = fs.find(
            self.root,
            lambda p: re.match('.*--format_json(-pretty)?$', p)
        )
        with ProcessPoolExecutor() as executor:
            self.executor = executor
            interests = await self.inspect_jsons(jsons)
        inspectors.merge_interests(
            self.interests,
            interests
        )
        return self.interests

    async def inspect_jsons(self, paths):
        if not paths:
            return dict()
        interests = dict()
        results = list(ProgressBar(
            self.executor.map(self._inspect_json, paths),
            total=len(paths),
            desc="Reading OCS files",
            disable=not self.progress,
        ))
        for result in results:
            interests.update(result)
        return interests

    @staticmethod
    def _inspect_json(path):
        result = {path: list()}
        if os.stat(path).st_size == 0:
            result[path].append("File is empty")
            return result
        with open(path) as fd:
            try:
                obj = json.load(fd)
            except json.decoder.JSONDecodeError:
                result[path].append("Failed to parse JSON content")
                return result
        if 'health_detail' in path:
            result[path].extend(OCS.unhealthy(obj))
        return result

    @staticmethod
    def unhealthy(obj):
        result = list()
        if obj['status'] != 'HEALTH_OK':
            result.append(obj)
        return result
