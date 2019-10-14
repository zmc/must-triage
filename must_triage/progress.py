import progress.bar


class NoProgress:
    def __init__(self, *args, **kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def next(self):
        pass

    def iter(self, it):
        for x in it:
            yield x

    def finish(self):
        pass


class ProgressBar(progress.bar.IncrementalBar):
    suffix = "%(index)d/%(max)d %(elapsed_td)s"
