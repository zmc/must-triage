import yaml

import asyncio
from concurrent.futures import ProcessPoolExecutor

import must_triage.fs as fs
import must_triage.inspectors as inspectors

from must_triage.inspectors.base import Inspector


class OCP(Inspector):
    async def inspect(self):
        self.interests = dict()
        yamls = fs.find(self.root, lambda p: fs.has_ext(p, ['.yaml', '.yml']))
        with ProcessPoolExecutor() as executor:
            self.executor = executor
            interests = await self.inspect_yamls(yamls)
        inspectors.merge_interests(
                self.interests,
                interests,
        )
        return self.interests

    async def inspect_yamls(self, paths):
        if not paths:
            return dict()
        interests = dict()
        #bar = self._progress_class("Reading OCP files", max=len(paths))
        bar = None
        loop = asyncio.get_running_loop()
        futures = [
            loop.run_in_executor(self.executor, OCP._inspect_yaml, path, bar)
            for path in paths
        ]
        results = await asyncio.gather(*futures, return_exceptions=False)
        for result in results:
            interests.update(result)
        if bar:
            bar.finish()
        return interests

    @staticmethod
    def _inspect_yaml(path, bar=None):
        result = {path: list()}
        with open(path) as fd:
            try:
                obj = yaml.safe_load(fd)
            except (yaml.scanner.ScannerError, yaml.parser.ParserError):
                result[path].append("Failed to parse YAML content")
                if bar:
                    bar.next()
                return result
        pods = list()
        if obj['kind'].lower() == 'pod':
            pods.append(obj)
        elif obj['kind'].lower() == 'podlist':
            pods.extend(filter(
                lambda o: o['kind'].lower() == 'pod',
                obj['items']
            ))
        result[path].extend(map(OCP.pod_ready, pods))
        # print(result)
        if bar:
            bar.next()
        return result

    @staticmethod
    def pod_ready(obj):
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
