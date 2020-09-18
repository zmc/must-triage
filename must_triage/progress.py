from tqdm import tqdm


class ProgressBar(tqdm):
    "A simple subclass of tqdm with our configuration items set"
    def __init__(self, *args, **kwargs):
        kwargs.update(dict(
            miniters=None,
            mininterval=0.1,
            maxinterval=1,
            smoothing=0,
            bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}]',
        ))
        super(ProgressBar, self).__init__(*args, **kwargs)

    @property
    def format_dict(self):
        d = super(ProgressBar, self).format_dict
        total_time = d["elapsed"] * (d["total"] or 0) / max(d["n"], 1)
        d.update(total_time=self.format_interval(total_time) + " in total")
        return d
