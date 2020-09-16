import pytest

import must_triage.inspectors as inspectors


class TestMergeInterests:
    @pytest.mark.parametrize(
        "existing,new,expected",
        [
            (
                dict(foo=['foo']),
                dict(bar=['bar']),
                dict(foo=['foo'], bar=['bar']),
            ),
            (
                dict(foo=['1']),
                dict(foo=['2']),
                dict(foo=['1', '2']),
            ),
            (
                dict(foo=['foo']),
                dict(bar=[]),
                dict(foo=['foo']),
            )
        ]
    )
    def test_merge(self, existing, new, expected):
        assert inspectors.merge_interests(existing, new) == expected


def test_all():
    inspector_names = list(map(lambda i: i.__name__, inspectors.all()))
    assert inspector_names == ['OCP', 'OCS']
