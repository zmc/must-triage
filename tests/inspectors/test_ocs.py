import json
import pytest

from unittest.mock import mock_open, patch

from must_triage.inspectors.ocs import OCS


class TestOCS:
    def teardown(self):
        patch.stopall()

    @pytest.mark.parametrize(
        "obj,expected",
        [
            (
                dict(status='HEALTH_OK'),
                list(),
            ),
            (
                dict(status='something else'),
                [dict(status='something else')],
            ),
        ]
    )
    def test_unhealthy(self, obj, expected):
        result = OCS.unhealthy(obj)
        assert (obj['status'] == 'HEALTH_OK') != (obj in result)

    @pytest.mark.parametrize(
        "path,obj",
        [
            (
                '/fake_path',
                None
            ),
            (
                '/fake_path',
                json.decoder.JSONDecodeError('', '', 0)
            ),
            (
                '/fake/health_detail',
                dict()
            ),
        ]
    )
    def test_inspect_json(self, path, obj):
        expected = None
        p_stat = patch('must_triage.inspectors.ocs.os.stat')
        m_stat = p_stat.start()
        if obj is None:
            m_stat.return_value.st_size = 0
            expected = ["File is empty"]
        else:
            m_stat.return_value.st_size = 1
        p_load = patch('must_triage.inspectors.ocs.json.load')
        m_load = p_load.start()
        if isinstance(obj, dict) or obj is None:
            m_load.return_value = obj
        else:
            m_load.side_effect = obj
            expected = ["Failed to parse JSON content"]
        p_unhealthy = patch('must_triage.inspectors.ocs.OCS.unhealthy')
        m_unhealthy = p_unhealthy.start()
        m_open = mock_open()
        with patch('must_triage.inspectors.ocs.open', m_open):
            result = OCS.inspect_json(path)
        if expected is None:
            assert m_unhealthy.call_count == 1
        else:
            assert expected == result[path]

    @pytest.mark.parametrize(
        "lines,panics",
        [
            (
                [
                    'we Observed a panic: here it is',
                ],
                1,
            ),
            (
                [
                    'no panic',
                ],
                0,
            ),
            (
                [
                    'we Observed a panic: here it is',
                    'no panic',
                    'Observed a panic:',
                ],
                2,
            ),
        ]
    )
    def test_inspect_log(self, lines, panics):
        path = '/fake_path'
        m_open = mock_open()
        with patch('must_triage.inspectors.ocs.open', m_open):
            m_open.return_value.readlines.return_value = lines
            result = OCS.inspect_log(path)
        assert len(result[path]) == panics
