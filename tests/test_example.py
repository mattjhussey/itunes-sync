"""Test example."""
import logging.config
from mock import patch
from robber import expect
import sys
import itunessync
from itunessync.__main__ import main


LOGGER = logging.getLogger(__name__)


def test_example():
    """Example test."""
    assert itunessync.example_function(42) == 42


def test_main_arg(caplog, capsys):
    """Test main uses arguments."""
    sys_args = ['exe.exe', '--expected_result', '35']
    with patch.object(sys, 'argv', sys_args), \
            patch.object(logging.config, 'fileConfig'):
        main()
    expect(caplog.text).to.contain('35')

    out, err = capsys.readouterr()
    expect(out).to.contain('35')


def test_main_no_arg(capsys):
    """Test main uses defaults."""
    sys_args = ['exe.exe']
    with patch.object(sys, 'argv', sys_args):
        main()

    out, err = capsys.readouterr()
    expect(out).to.contain('7')


def test_caplog_ok(caplog):
    """Check that caplog hasn't been corrupted.

    If the fileconfig is called under testing then then caplog stops working.
    """
    LOGGER.debug('thing')
    expect(caplog.text).to.contain('thing')
