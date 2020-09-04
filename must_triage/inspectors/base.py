from concurrent.futures import ProcessPoolExecutor

import must_triage.fs as fs
import must_triage.inspectors as inspectors
from must_triage.progress import ProgressBar


class Inspector:
    def __init__(self, root, progress=False):
        self.root = root
        self.progress = progress

    def has_method(self, name):
        return callable(getattr(self, name, None))

    def gather(self):
        self.gathered = dict()
        for type_, obj in self.gather_types.items():
            # this assert is mainly to help diagnose unexpected failures
            assert 'match' in obj
            self.gathered[type_] = fs.find(self.root, obj['match'])

    async def inspect(self):
        self.interests = dict()
        with ProcessPoolExecutor() as executor:
            for type_, paths in self.gathered.items():
                func = getattr(self, f"inspect_{type_}", None)
                if not func:
                    continue
                description = self.gather_types[type_].get(
                    'description', f"Inspecting {type_}")
                interests = await self._inspect_helper(
                    executor,
                    paths,
                    func,
                    description,
                )
                inspectors.merge_interests(self.interests, interests)
        return self.interests

    async def _inspect_helper(self, executor, paths, func, description):
        if not paths:
            return dict()
        interests = dict()
        results = list(ProgressBar(
            executor.map(func, paths),
            total=len(paths),
            desc=description,
            disable=not self.progress,
        ))
        for result in results:
            interests.update(result)
        return interests
