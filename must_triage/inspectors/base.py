class Inspector:
    def __init__(self, root, progress=False):
        self.root = root
        self.progress = progress

    async def inspect(self):
        raise NotImplementedError
