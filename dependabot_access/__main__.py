import sys
import logging

from . import access

logging.basicConfig(level=logging.INFO)

failed = False


def handle_error(err):
    global failed
    logging.error(err)
    failed = True


def main(name):
    if name == '__main__':
        access.configure_app(sys.argv[1:], handle_error)

        if failed:
            print('error(s) were encountered - see above', file=sys.stderr)
            sys.exit(1)


main(__name__)
