import json
import os
import re

import must_triage.fs as fs
import must_triage.inspectors.base as base


class OCS(base.Inspector):
    gather_types = dict(
        json=dict(
            match=lambda p: re.match('.*--format_json(-pretty)?$', p),
            description="Reading OCS JSON files",
        ),
        log=dict(
            match=lambda p: fs.has_ext(p, ['log']),
            description="Reading OCS log files",
        ),
    )

    @staticmethod
    def inspect_json(path):
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

    @staticmethod
    def inspect_log(path):
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
