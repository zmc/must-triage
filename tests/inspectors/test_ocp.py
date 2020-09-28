import pytest
import yaml

from unittest.mock import mock_open, patch

from must_triage.inspectors.ocp import OCP


class TestOCP:
    def teardown(self):
        patch.stopall()

    @pytest.mark.parametrize(
        "obj",
        [
            (
                yaml.scanner.ScannerError
            ),
            (
                dict(kind='pod')
            ),
            (
                dict(
                    kind='podList',
                    items=[
                        dict(kind='pod'),
                        dict(kind='pod'),
                    ],
                )
            ),
            (
                dict(error='something')
            ),
        ]
    )
    def test_inspect_yaml(self, obj):
        path = '/fake_path'
        p_safe_load = patch('must_triage.inspectors.ocp.yaml.safe_load')
        m_safe_load = p_safe_load.start()
        p_operator_success = patch(
            'must_triage.inspectors.ocp.OCP.operator_success')
        m_operator_success = p_operator_success.start()
        p_pod_ready = patch('must_triage.inspectors.ocp.OCP.pod_ready')
        m_pod_ready = p_pod_ready.start()
        m_open = mock_open()
        with patch('must_triage.inspectors.ocp.open', m_open):
            if isinstance(obj, dict):
                m_safe_load.return_value = obj
            else:
                m_safe_load.side_effect = obj
            result = OCP.inspect_yaml(path)
        if not isinstance(obj, dict):
            assert result[path] == ["Failed to parse YAML content"]
            return
        assert len(m_operator_success.call_args_list) == \
            len(list(filter(lambda o: 'kind' in o, obj)))

        def pods_count(obj):
            kind = obj.get('kind', '').lower()
            if kind == 'pod':
                return 1
            if kind == 'podlist':
                return len(
                    [o for o in obj['items'] if o['kind'].lower() == 'pod']
                )
            return 0

        assert len(m_pod_ready.call_args_list) == pods_count(obj)

        if 'error' in obj:
            assert obj in result[path]

    @pytest.mark.parametrize(
        "obj,expected",
        [
            (
                dict(
                    kind='ClusterServiceVersion',
                    status=dict(phase='succeeded'),
                ),
                list()
            ),
            (
                dict(
                    kind='ClusterServiceVersion',
                    status=dict(phase='other'),
                ),
                ["Operator phase is 'other', not 'Succeeded' as expected"]

            ),
            (
                dict(kind='other'),
                list()
            )
        ]
    )
    def test_operator_success(self, obj, expected):
        result = OCP.operator_success(obj)
        assert result == expected

    @pytest.mark.parametrize(
        "obj,expected",
        [
            (
                dict(
                    metadata=dict(name='test_pod'),
                    status=dict(containerStatuses=[
                        dict(
                            name='test_container',
                            ready=False,
                            state=dict(
                                terminated=dict(
                                    reason='garbage',
                                ),
                            ),
                        ),
                    ]),
                ),
                ["Container 'test_container' in pod 'test_pod' is not ready"],
            ),
            (
                dict(
                    metadata=dict(name='test_pod'),
                    status=dict(containerStatuses=[
                        dict(
                            name='test_container',
                            ready=False,
                            state=dict(
                                terminated=dict(
                                    reason='completed',
                                    exitCode=0,
                                ),
                            ),
                        ),
                    ]),
                ),
                list(),
            ),
            (
                dict(
                    metadata=dict(name='test_pod'),
                    status=dict(),
                ),
                [dict(
                    pod_name='test_pod',
                    status=dict(),
                )],
            ),
        ]
    )
    def test_pod_ready(self, obj, expected):
        result = OCP.pod_ready(obj)
        assert result == expected
