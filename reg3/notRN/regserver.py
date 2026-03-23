#!/usr/bin/env python

#-----------------------------------------------------------------------
# regserver.py
# Author: Saleema Diallo & Ludan Alsoudani
#-----------------------------------------------------------------------

import sys
import os
import json
import contextlib
import argparse
import sqlite3
import socket
import threading
import time



DATABASE_URL = 'file:reg.sqlite'

#-----------------------------------------------------------------------

try:
    IODELAY = int(os.environ.get('IODELAY', '0'))
except ValueError:
    IODELAY = 0

try:
    CDELAY = int(os.environ.get('CDELAY', '0'))
except ValueError:
    CDELAY = 0

#-----------------------------------------------------------------------

def consume_cpu_time(delay):
    initial_thread_time = time.thread_time()
    while (time.thread_time() - initial_thread_time) < delay:
        pass

#-----------------------------------------------------------------------


class ChildThread(threading.Thread):
    def __init__(self, either_args, sock):
        threading.Thread.__init__(self)
        self._either_args = either_args
        self._sock = sock

    def run(self):
        print('spawning child thread')
        print("recieved request:", self._either_args)
        #using what is read from client
        with self._sock:
            # Simulate a compute-bound server.
            consume_cpu_time(CDELAY)
            # Simulate an I/O-bound server
            time.sleep(IODELAY)

            if self._either_args[0] == 'get_overviews':
                handle_overviews(
                    self._sock,
                    self._either_args[1].get('dept'),
                    self._either_args[1].get('coursenum'),
                    self._either_args[1].get('area'),
                    self._either_args[1].get('title')
                    )

            elif self._either_args[0] == 'get_details':
                handle_details(self._sock, self._either_args[1])
        print('Closed socket in child thread')
        print('Exiting child thread')

#-----------------------------------------------------------------------

def handle_overviews(sock, dept, coursenum, area, title):
    try:
        with contextlib.closing(sqlite3.connect(DATABASE_URL + \
            '?mode=ro', isolation_level=None, uri=True)) as connection:
            with contextlib.closing(connection.cursor()) as cursor:
                statement_str = '''SELECT classes.classid, \
                    crosslistings.dept, crosslistings.coursenum, \
                        courses.area,  courses.title
                    FROM classes, courses, crosslistings
                    WHERE classes.courseid=courses.courseid 
                    AND crosslistings.courseid = courses.courseid  
                    AND dept LIKE ? 
                    AND coursenum LIKE ? 
                    AND area LIKE ? 
                    AND title LIKE ? 
                    ORDER BY crosslistings.dept, crosslistings.coursenum, classes.classid
                    '''
                cursor.execute(statement_str,
                (f"%{dept}%", f"%{coursenum}%", \
                    f"%{area}%", f"%{title}%"))
                table = cursor.fetchall()


                protocol = [True, []]
                for row in table:
                    protocol[1].append(
                        {'classid':row[0], 'dept':row[1],
                        'coursenum':row[2], 'area':row[3], \
                            'title':row[4]})

                json_str = json.dumps(protocol)

                with sock.makefile(mode='w', encoding='utf-8') as flo:
                    flo.write(json_str + '\n')
                    flo.flush()

                print('wrote to client')
    except sqlite3.OperationalError as ex:
        protocol = [False, \
            "A server error occurred. " + \
                "Please contact the system administrator."]
        json_str = json.dumps(protocol)
        print(f'{sys.argv[0]}: {ex}', file=sys.stderr)
        try:
            with sock.makefile(mode='w', encoding='utf-8') as flo:
                flo.write(json_str + '\n')
                flo.flush()
        except Exception as thing:
            print(f'{sys.argv[0]}: {thing}', file=sys.stderr)

    except Exception as ex:
        print(f'{sys.argv[0]}: {ex}', file=sys.stderr)

#-----------------------------------------------------------------------

def handle_details(sock, classid):
    try:
        with contextlib.closing(sqlite3.connect(DATABASE_URL + \
            '?mode=ro', isolation_level=None, uri=True)) as connection:
            with contextlib.closing(connection.cursor()) as cursor:
                statement_str = '''SELECT classid, days, starttime,
                    endtime, bldg, roomnum, courseid
                    FROM classes
                    WHERE classid = ?
                    ORDER BY classid ASC
                    '''
                cursor.execute(statement_str, [classid])
                classdeets = cursor.fetchall()
                if len(classdeets) == 0:
                    protocol = [False, \
                        f"no class with classid {classid} exists"]
                    json_str = json.dumps(protocol)
                    with sock.makefile(mode='w', \
                        encoding='utf-8') as flo:
                        flo.write(json_str + '\n')
                        flo.flush()
                    raise KeyError()
                statement_str = '''SELECT courseid, area, title, \
                    descrip, prereqs
                   FROM courses
                   WHERE courseid = ?
                   '''
                cursor.execute(statement_str, [classdeets[0][6]])
                coursedeets = cursor.fetchall()

                statement_str = '''SELECT dept, coursenum
                   FROM crosslistings
                   WHERE courseid = ?
                   ORDER BY coursenum, dept ASC
                   '''
                cursor.execute(statement_str, [classdeets[0][6]])
                dept_and_num = cursor.fetchall()

                statement_str = '''SELECT coursesprofs.courseid,\
                     coursesprofs.profid, profs.profid, profs.profname
                   FROM coursesprofs, profs
                   WHERE courseid = ?
                   AND coursesprofs.profid = profs.profid
                   ORDER BY profs.profname ASC
                   '''
                cursor.execute(statement_str, [classdeets[0][6]])
                profname = cursor.fetchall()

                profs=[]
                deptnum=[]
                for row in profname:
                    profs.append(row[3])
                for row in dept_and_num:
                    deptnum.append({'dept':row[0], 'coursenum':row[1]})

                protocol = [True, {
                    'classid':classdeets[0][0],
                    'days':classdeets[0][1],
                    'starttime':classdeets[0][2],
                    'endtime':classdeets[0][3],
                    'bldg':classdeets[0][4],
                    'roomnum':classdeets[0][5],
                    'courseid':classdeets[0][6],
                    'deptcoursenums':deptnum,
                    'area':coursedeets[0][1],
                    'title':coursedeets[0][2],
                    'descrip':coursedeets[0][3],
                    'prereqs':coursedeets[0][4],
                    'profnames':profs
                }]

                json_str = json.dumps(protocol)
                with sock.makefile(mode='w', encoding='utf-8') as flo:
                    flo.write(json_str + '\n')
                    flo.flush()
                print('wrote to client')

    except sqlite3.OperationalError as ex:
        protocol = [False, \
            "A server error occurred. " + \
                "Please contact the system administrator."]
        json_str = json.dumps(protocol)
        print(f'{sys.argv[0]}: {ex}', file=sys.stderr)
        try:
            with sock.makefile(mode='w', encoding='utf-8') as flo:
                flo.write(json_str + '\n')
                flo.flush()
        except Exception as thing:
            print(f'{sys.argv[0]}: {thing}', file=sys.stderr)
    except KeyError:
        pass
    except Exception as ex:
        print(f'{sys.argv[0]}: {ex}', file=sys.stderr)



#-----------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description = \
        "Server for the registrar application")
    parser.add_argument('port', type=int, \
        help='the port at which the server is listening')
    args = parser.parse_args()

    try:
        server_sock = socket.socket()
        print('opened server socket')
        if os.name != 'nt':
            server_sock.setsockopt(socket.SOL_SOCKET, \
                socket.SO_REUSEADDR, 1)
        server_sock.bind(('', int(args.port)))
        print('Bound server socket to port')
        server_sock.listen()
        print('Listening')
        while True:
            try:
                sock, _ = server_sock.accept()
                print('Accepted connection, opened socket')
                #readings from client
                with sock.makefile(mode='r', encoding='utf-8') as flo:
                    json_str = flo.readline()
                json_str = json_str.rstrip()
                either_args = json.loads(json_str)
                child = ChildThread(either_args, sock)
                child.start()

            except Exception as ex:
                print(f'{sys.argv[0]}: {ex}', file=sys.stderr)
    except Exception as ex:
        print(f'{sys.argv[0]}: {ex}', file=sys.stderr)


if __name__ == '__main__':
    main()
