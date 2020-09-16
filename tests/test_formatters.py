import datetime
import pytest

from must_triage import formatters


@pytest.mark.parametrize(
    "obj,expected",
    [
        (
            datetime.datetime.utcfromtimestamp(1600469633.228982),
            "2020-09-18 22:53:53.228982"
        ),
        (
            True,
            None
        ),
    ]
)
def test_json_serializer(obj, expected):
    assert formatters.json_serialize(obj) == expected
