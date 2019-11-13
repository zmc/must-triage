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
        logs = fs.find(
            self.root,
            lambda p: fs.has_ext(p, ['log'])
        )
        with ProcessPoolExecutor() as executor:
            self.executor = executor
            json_interests = await self.inspect_jsons(jsons)
            log_interests = await self.inspect_logs(logs)
        inspectors.merge_interests(
            self.interests,
            json_interests
        )
        inspectors.merge_interests(
            self.interests,
            log_interests
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

    async def inspect_logs(self, paths):
        if not paths:
            return dict()
        interests = dict()
        results = list(ProgressBar(
            self.executor.map(OCS._inspect_log, paths),
            total=len(paths),
            desc="Reading log files",
            disable=not self.progress,
        ))
        for result in results:
            interests.update(result)
        return interests

    @staticmethod
    def _inspect_log(path):
        result = {path: list()}
        with open(path) as log:
            for line in log.readlines():
                line = line.strip()
                if OCS.panicked(line):
                    result[path].append(line)
        return result

    @staticmethod
    def panicked(line):
        if re.match('.*Observed a panic:.*', line):
            return True
        return False
