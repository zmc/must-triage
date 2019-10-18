from must_triage.progress import NoProgress


class Inspector:
    def __init__(self, root, progress_class=NoProgress):
        self.root = root
        self._progress_class = progress_class

    async def inspect(self):
        raise NotImplementedError
