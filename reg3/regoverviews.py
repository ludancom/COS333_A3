#!/usr/bin/env python

#-----------------------------------------------------------------------
# regoverviews.py
# Author: Saleema Diallo & Ludan Alsoudani
#-----------------------------------------------------------------------

import sys
import argparse
import textwrap
import socket
import json

#-----------------------------------------------------------------------
def main():
    try:
        parser = argparse.ArgumentParser(description = \
            "Registrar application: show overviews of classes")
        parser.add_argument("-d", metavar="dept", \
            help='show only those classes \
                whose department contains dept')
        parser.add_argument('-n', type=int, metavar='num', \
            help='show only those classes \
                whose course number contains num')
        parser.add_argument('-a', metavar='area', \
            help='show only those classes \
                whose distrib area contains area')
        parser.add_argument('-t', metavar='title', \
            help='show only those classes \
                whose course title contains title')
        parser.add_argument('host', help='the computer \
            on which the server is running')
        parser.add_argument('port', type=int, help='the port at \
            which the server is listening')
        args = parser.parse_args()


        coursenum = ''
        dept = ''
        area = ''
        title = ''

        if args.n:
            coursenum = args.n
        if args.d:
            dept = args.d
        if args.t:
            title = args.t
        if args.a:
            area = args.a

        protocol = ['get_overviews',
        {'dept':dept, 'coursenum':coursenum, \
            'area':area, 'title':title}]

        with socket.socket() as sock:
            sock.connect((args.host, int(args.port)))
            #writing to outside
            json_str = json.dumps(protocol)
            with sock.makefile(mode='w', encoding='utf-8') as flo:
                flo.write(json_str + '\n')
                flo.flush()

            #readings from outside
            with sock.makefile(mode='r', encoding='utf-8') as flo:
                json_read = flo.readline()

            json_read = json_read.rstrip()
            json_read = json.loads(json_read)

            if json_read[0] is False:
                raise Exception(json_read[1])


            wrapper = textwrap.TextWrapper(width=72, \
            subsequent_indent = '                       ')

            print("ClsId Dept CrsNum Area Title")
            print("----- ---- ------ ---- -----")

            for row in json_read[1]:
                row = '%5s %4s %6s %4s %s' % (row.get('classid'),
                 row.get('dept'), row.get('coursenum'), \
                    row.get('area'), row.get('title'))
                row = wrapper.wrap(text=row)
                for element in row:
                    print(element)


    except Exception as ex:
        print(f'{sys.argv[0]}: {ex}', file=sys.stderr)
        sys.exit(2)

if __name__ == '__main__':
    main()
