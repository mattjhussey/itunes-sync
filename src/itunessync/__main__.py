"""Main entry point."""
from argparse import ArgumentParser
import logging
import logging.config
import sys
import pkg_resources
from .example_module import example_function


LOGGER = logging.getLogger(__name__)


def main():
    """Main entry point."""
    log_path = pkg_resources.resource_filename(__name__, "logging.conf")
    logging.config.fileConfig(log_path,
                              disable_existing_loggers=False)

    parser = ArgumentParser(description='Example Python')
    parser.add_argument('--expected_result',
                        action='store',
                        type=int,
                        default=7,
                        help='The expected result (default: %(default)s)')

    parsed = parser.parse_args(sys.argv[1:])

    result = example_function(parsed.expected_result)

    print result
    LOGGER.debug('Result: %s', result)


if __name__ == '__main__':
    print main()
