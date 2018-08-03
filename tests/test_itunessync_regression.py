"""Regression tests for itunessync."""
from os.path import dirname, realpath
import py
import pytest
import sys
from mock import patch
from robber import expect
from itunessync.__main__ import main


def test_music_sync(itunes_library_xml, tmpdir, local_test_dir):
    """Test running a sync on a known directory."""
    # Create populated sdcard directory
    sdcard = tmpdir.mkdir('sdcard')

    # Create an old m3u file
    sdcard.join('old.m3u').write('old')

    # Create an empty directory expected to be deleted
    todelete_empty = sdcard.mkdir('todelete_empty')

    # Create a folder with pamp file expected to be deleted
    todelete_pamp = sdcard.mkdir('todelete_pamp')
    todelete_pamp.join('albumart.pamp').write('delete')

    # Create a folder with unneeded music expected to be deleted
    todelete_noneed = sdcard.mkdir('todelete_noneed')
    todelete_noneed.join('unwanted.m4a').write('delete')

    sys_args = ['exe.exe', str(itunes_library_xml), 'tocopy']
    with patch.object(sys, 'argv', sys_args), \
            sdcard.as_cwd():
        main()

    # Expect empty directories to be removed
    expect(todelete_empty.check()).to.be.false()
    expect(todelete_pamp.check()).to.be.false()
    expect(todelete_noneed.check()).to.be.false()

    # Expect music to have been copied
    expect(
        (sdcard / 'Someone_' / 'An Album').join('a.mp3').check()).to.be.true()
    expect(
        (sdcard / 'Someone' / 'An Album').join('b.m4a').check()).to.be.true()
    expect(
        (sdcard / 'Someone' / 'An Album').join('c.m4a').check()).to.be.true()
    expect(
        (sdcard / 'Someone' / 'An Album').join('d.m4a').check()).to.be.true()
    expect(
        (sdcard / 'Someone' / 'An Album').join('e.m4a').check()).to.be.true()

    # Expect m3u files to have been deleted if old
    expect(sdcard.join('old.m3u')).to.be.false()

    # Expect m3u files to have been created
    expect(sdcard.join('Alter Bridge.m3u').check()).to.be.true()
    expect(sdcard.join('Library.m3u').check()).to.be.true()
    expect(sdcard.join('Music.m3u').check()).to.be.true()
    expect(sdcard.join('something.m3u').check()).to.be.true()
    expect(sdcard.join('tocopy.m3u').check()).to.be.true()

    # Expect m3u files to contain correct data
    expect(
        sdcard.join('Alter Bridge.m3u').readlines()). \
        to.eq(local_test_dir.join('Alter Bridge.m3u').readlines())
    expect(
        sdcard.join('Library.m3u').readlines()). \
        to.eq(local_test_dir.join('Library.m3u').readlines())
    expect(
        sdcard.join('Music.m3u').readlines()). \
        to.eq(local_test_dir.join('Music.m3u').readlines())
    expect(
        sdcard.join('something.m3u').readlines()). \
        to.eq(local_test_dir.join('something.m3u').readlines())
    expect(
        sdcard.join('tocopy.m3u').readlines()). \
        to.eq(local_test_dir.join('tocopy.m3u').readlines())


# Test with a playlist that doesn't exist


@pytest.fixture
def local_test_dir():
    """Return the local test directory.

    Used to reference test files.
    """
    return py.path.local(dirname(realpath(__file__)))


@pytest.fixture
def itunes_library_xml(local_test_dir, tmpdir):
    """Return an example itunes library file.

    The itunes library references files in the test directory.
    """
    # Copy the xml library to the temporary directory
    real_library_xml = local_test_dir / 'itunes_valid.xml'
    target = tmpdir / 'itunes_valid.xml'
    real_library_xml.copy(target)

    # Replace the {{musicdir}} placeholders with the directory
    # of the real music files
    with open(str(target), 'r') as f:
        data = f.read()
    music_dir_path = str(local_test_dir).replace('\\', '/')
    data = data.replace('{{musicdir}}', music_dir_path)
    with open(str(target), 'w') as f:
        f.write(data)

    return target
