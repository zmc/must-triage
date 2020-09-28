import argparse
import pytest

from unittest.mock import patch

from must_triage import cmd


def test_parse_args():
    args = ['.']
    parsed = cmd.parse_args(args)
    assert parsed.quiet is False
    assert parsed.out == 'json'
    assert parsed.path == '.'


def test_parse_args_bad_path():
    args = ['/fake_path_here']
    with pytest.raises((argparse.ArgumentError, SystemExit)):
        cmd.parse_args(args)


class TestMain:
    def teardown(self):
        patch.stopall()

    @pytest.mark.parametrize(
        "args",
        [
            ['must-triage', '.'],
            ['must-triage', '-o', 'yaml', '.'],
        ]
    )
    def test_main(self, args):
        p_argv = patch(
            'must_triage.cmd.sys.argv', args)
        p_argv.start()
        p_ocp = patch('must_triage.cmd.inspectors.ocp.OCP', autospec=True)
        m_ocp = p_ocp.start()
        m_ocp.return_value.inspect.return_value = dict()
        p_ocs = patch('must_triage.cmd.inspectors.ocs.OCS', autospec=True)
        m_ocs = p_ocs.start()
        m_ocs.return_value.inspect.return_value = dict()
        p_all = patch('must_triage.cmd.inspectors.all')
        m_all = p_all.start()
        m_all.return_value = [m_ocp, m_ocs]
        p_merge = patch('must_triage.cmd.inspectors.merge_interests')
        m_merge = p_merge.start()
        p_dumps = patch('must_triage.cmd.json.dumps')
        m_dumps = p_dumps.start()
        p_safe_dump = patch('must_triage.cmd.yaml.safe_dump')
        m_safe_dump = p_safe_dump.start()
        cmd.main()
        assert m_all.call_count == 1
        assert m_ocp.return_value.gather.call_count == 1
        assert m_ocp.return_value.inspect.await_count == 1
        assert m_ocs.return_value.gather.call_count == 1
        assert m_ocs.return_value.inspect.await_count == 1
        assert m_merge.call_count == 2
        if 'yaml' in args:
            assert m_safe_dump.call_count == 1
        else:
            assert m_dumps.call_count == 1
