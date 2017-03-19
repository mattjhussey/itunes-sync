"""Example module."""
import logging


LOGGER = logging.getLogger(__name__)


def example_function(result):
    """Example function."""
    LOGGER.debug('Example: %s', result)
    return result
