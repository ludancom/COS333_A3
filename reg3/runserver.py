#!/usr/bin/env python

#-----------------------------------------------------------------------
# runserver.py
# Author: Saleema Diallo & Ludan Alsoudani
#-----------------------------------------------------------------------

import sys
import argparse
import regoverviews

def main():
    try:
        parser = argparse.ArgumentParser(description = \
            "The registrar application")
        parser.add_argument('port', type=int, help='the port at \
            which the server should listen')
        args = parser.parse_args()
        port = args.port
        regoverviews.app.run('0.0.0.0', port, debug=True)
        print('Listening on port ' + str(port))
        httpd.serve_forever()


    except Exception as ex:
        print(f'{sys.argv[0]}: {ex}', file=sys.stderr)
        sys.exit(2)

if __name__ == '__main__':
    main()
