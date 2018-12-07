import unittest
from unittest.mock import patch

from dependabot_access import __main__


class TestMain(unittest.TestCase):

    @patch('dependabot_access.__main__.failed')
    @patch('dependabot_access.__main__.logging')
    def test_handle_error(self, logging, failed):
        # given
        err = 'An error!'

        # when
        __main__.handle_error(err)

        # then
        logging.error.assert_called_once_with(err)
        assert failed

    @patch('dependabot_access.__main__.access')
    def test_main(self, access):
        # given when
        __main__.main('__main__')

        # then
        access.configure_app.assert_called()

    @patch('dependabot_access.__main__.failed', True)
    @patch('dependabot_access.__main__.sys')
    @patch('dependabot_access.__main__.access')
    def test_main_failed(self, access, sys):
        # given when
        __main__.main('__main__')

        # then
        sys.exit.assert_called_once_with(1)
