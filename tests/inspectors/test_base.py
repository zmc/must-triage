import logging
import pytest

from concurrent.futures import ProcessPoolExecutor
from unittest.mock import patch

from must_triage.inspectors.base import Inspector


@pytest.fixture
def inspector(request):
    obj = Inspector(root='/tmp/must_triage_tests', progress=False)
    return obj


class TestInspector:
    def teardown(self):
        patch.stopall()

    def test_init(self, inspector):
        assert inspector.root == '/tmp/must_triage_tests'
        assert inspector.progress is False
        assert isinstance(inspector.log, logging.Logger)

    def test_gather(self, inspector):
        inspector.gather_types = dict(
            jpg=dict(
                match=None,
                description='desc',
            )
        )
        with patch('must_triage.inspectors.base.fs.find') as m_find:
            m_find.return_value = 'path'
            inspector.gather()
        assert m_find.call_count == len(inspector.gather_types.keys())
        assert len(inspector.gathered.keys()) == m_find.call_count

    @pytest.mark.asyncio
    async def test_inspect(self, inspector):
        inspector.gather_types = dict(
            jpg=dict(),
            png=dict(),
        )
        inspector.gathered = dict(
            jpg=['1', '2'],
            gif=['3', '4'],
            png=['5', '6'],
        )
        inspector.inspect_jpg = True
        inspector.inspect_png = True
        p_helper = patch(
            'must_triage.inspectors.base.Inspector._inspect_helper')
        m_helper = p_helper.start()
        m_helper.return_value = dict()
        await inspector.inspect()
        assert m_helper.call_count == 2  # once each for jpg, png

    @staticmethod
    def _dummy_inspector(path):
        return {path: [f"inspected {path}"]}

    @pytest.mark.asyncio
    async def test_inspect_helper(self, inspector):
        paths = ['/foo', '/bar']

        with ProcessPoolExecutor() as executor:
            result = await inspector._inspect_helper(
                executor, paths, self._dummy_inspector, "description")

        for key, value in result.items():
            assert len(value) == 1
            assert value[0] == f"inspected {key}"

    @pytest.mark.asyncio
    async def test_inspect_helper_noop(self, inspector):
        result = await inspector._inspect_helper(
            None, [], None, None)
        assert result == dict()

    def test_inspector_wrapper_exc(self, inspector):

        def func(*args):
            raise Exception

        result = inspector._inspector_wrapper(func, '')
        assert result == dict()
