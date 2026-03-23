#!/usr/bin/env python

#-----------------------------------------------------------------------
# regdetails.py
# Author: Saleema Diallo & Ludan Alsoudani
#-----------------------------------------------------------------------

import sys
import argparse
import textwrap
import socket
import json

DATABASE_URL = 'file:reg.sqlite'

def main():
    try:
        parser = argparse.ArgumentParser(description =
        "Registrar application: show details about a class")
        parser.add_argument('host', help='the computer on which the \
            server is running')
        parser.add_argument('port', type=int, help='the port at which the server \
            is listening')
        parser.add_argument('classid', type=int,
        help='the id of the class whose details should be shown')
        args = parser.parse_args()
        classid = args.classid

        host = args.host
        port = int(args.port)

        protocol = ['get_details', classid]
        with socket.socket() as sock:
            sock.connect((host, port))
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
                    subsequent_indent = '   ')

            print("-------------")
            print("Class Details")
            print("-------------")

            print(("Class Id: " + \
                str(json_read[1].get('classid'))).strip())
            print(("Days: " + str(json_read[1].get('days'))).strip())
            print(("Start time: " + \
                str(json_read[1].get('starttime'))).strip())
            print(("End time: " + \
                str(json_read[1].get('endtime'))).strip())
            print(("Building: " + \
                str(json_read[1].get('bldg'))).strip())
            print(("Room: " + str(json_read[1].get('roomnum'))).strip())

            print("--------------")
            print("Course Details")
            print("--------------")

            print("Course Id: "+ str(json_read[1].get('courseid')))
            for row in json_read[1].get('deptcoursenums'):
                print(("Dept and Number: " + str(row.get('dept')) + \
                    " " + str(row.get('coursenum'))).strip())

            print(("Area: " + str(json_read[1].get('area'))).strip())
            word_list = wrapper.wrap(text="Title: " + \
                    str(json_read[1].get('title')))
            for element in word_list:
                print(element)

            word_list = wrapper.wrap(text="Description: " \
                    + str(json_read[1].get('descrip')))
            for element in word_list:
                print(element)

            word_list = wrapper.wrap(text="Prerequisites: "\
                    + str(json_read[1].get('prereqs')))
            for element in word_list:
                print(element)

            for row in json_read[1].get('profnames'):
                print(("Professor: " + str(row)).strip())

    except Exception as ex:
        print(f'{sys.argv[0]}: {ex}', file=sys.stderr)
        sys.exit(2)

if __name__ == '__main__':
    main()
