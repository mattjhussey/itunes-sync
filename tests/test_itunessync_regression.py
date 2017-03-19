from mock import patch
import os
from os.path import dirname, realpath
import py
import pytest
import shutil
import itunessync.itunessync
from itunessync.itunessync import doStuff, getExtensionFiles


def test_valid_file(tmpdir, itunes_valid, itunes_music_valid):
    sdcard = tmpdir / 'sdcard'
    sdcard.mkdir()
    todelete = sdcard / 'todelete'
    todelete.mkdir()
    todelete.join('albumart.pamp').write('delete')
    notneeded = sdcard / 'notneeded'
    notneeded.mkdir()
    notneeded.join('notneeded.m4a').write('delete')
    real_getExtensionFiles = getExtensionFiles
    real_osRemove = os.remove
    def mock_copy(src, target):
        py.path.local('..' + src[2:]).copy(py.path.local(target))
    def mock_getExtensionFiles(extension):
        found = set(['.\\' + f[1:] for f in real_getExtensionFiles(extension)])
        return found
    def mock_remove(file):
        if file.startswith('.\/'):
            real_osRemove(file[3:])
        else:
            real_osRemove(file)
    with patch.object(shutil, 'copy') as file_copy, \
           patch.object(itunessync.itunessync, 'getExtensionFiles') as getExFiles, \
           patch.object(os, 'remove') as os_remove, \
           sdcard.as_cwd():
        file_copy.side_effect = mock_copy
        getExFiles.side_effect = mock_getExtensionFiles
        os_remove.side_effect = mock_remove
        doStuff(str(itunes_valid), 'tocopy')


@pytest.fixture
def local_dir():
    return py.path.local(dirname(realpath(__file__)))


@pytest.fixture
def itunes_valid(local_dir, tmpdir):
    fixture = local_dir / 'itunes_valid.xml'
    target = tmpdir / 'itunes_valid.xml'
    fixture.copy(target)
    return target


@pytest.fixture
def itunes_music_valid(local_dir, tmpdir):
    music_dir = tmpdir / 'music'
    music_dir.mkdir()
    files = (
        'a.m4a',
        'b.m4a',
        'c.m4a',
        'd.m4a',
        'e.m4a',)
    for f in files:
        source = local_dir / f
        target = music_dir / f
        source.copy(target)
    return music_dir
