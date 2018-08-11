"""Main entry point."""
from argparse import ArgumentParser
import sys
import pkg_resources
from .itunessync import do_stuff


def main():
    """Run a sync from the command line."""
    parser = ArgumentParser(
        description='iTunes Sync. '
        'Syncs music in an iTunes library to a directory')
    parser.add_argument('itunes_library')
    parser.add_argument('itunes_playlist')

    parsed = parser.parse_args(sys.argv[1:])

    do_stuff(parsed.itunes_library, parsed.itunes_playlist)


if __name__ == '__main__':
    import logging.config
    LOG_PATH = pkg_resources.resource_filename(__name__, "logging.conf")
    logging.config.fileConfig(LOG_PATH,
                              disable_existing_loggers=False)

    print main()
