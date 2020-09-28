import pyfakefs
import pytest

from unittest.mock import patch

import must_triage.fs


@pytest.mark.parametrize(
    "path,ext,expected",
    [
        (
            '/a/jpeg', 'jpeg', False
        ),
        (
            '/a.jpeg', 'jpeg', True
        ),
        (
            'a.yml', ['yaml', 'yml'], True
        ),
        (
            'a.yaml', '.json', False
        ),
    ]
)
def test_has_ext(path, ext, expected):
    assert must_triage.fs.has_ext(path, ext) is expected


@pytest.mark.parametrize(
    "files,path,callback,expected",
    [
        (
            [
                dict(path='/a/b/c/d.yaml'),
                dict(path='/a/b/c/d.json'),
                dict(path='/a/b/c/d/e.yaml'),
                dict(path='/1/2/3/4.yaml'),
            ],
            '/a',
            lambda p: p.endswith('.yaml'),
            [
                '/a/b/c/d.yaml',
                '/a/b/c/d/e.yaml',
            ]
        ),
        (
            [
                dict(path='/a/b.log'),
            ],
            '/a/b.log',
            lambda p: p.endswith('log'),
            [
                '/a/b.log',
            ]
        ),
        (
            [
                dict(path='/1/2/3.txt'),
                dict(path='/4/5/6.tar.gz'),
                dict(path='/7/8/9.so'),
            ],
            '/',
            lambda p: False,
            []
        ),
    ]
)
def test_fs(fs, files, path, callback, expected):
    for f in files:
        fs.create_file(
            f['path'],
            contents=f.get('contents', ''),
        )
    result = must_triage.fs.find(path, callback)
    assert result == expected
