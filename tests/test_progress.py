import pytest

from must_triage import progress


@pytest.fixture
def obj(request):
    return progress.ProgressBar()


class TestProgressBar:
    def test_init(self, obj):
        assert obj.mininterval == 0.1
        assert obj.maxinterval == 1
        assert obj.smoothing == 0
        assert obj.bar_format == \
            '{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}]'

    def test_format_dict(self, obj):
        assert 'total_time' in obj.format_dict
