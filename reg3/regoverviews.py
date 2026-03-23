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

import contextlib
import sqlite3
import flask
import html

#-----------------------------------------------------------------------

DATABASE_URL = 'file:reg.sqlite'

#-----------------------------------------------------------------------

app = flask.Flask(__name__, template_folder='.')

#-----------------------------------------------------------------------

@app.route('/', methods=['GET'])
@app.route('/searchfrom', methods =['GET'])
def searchfrom():
    html_code = flask.render_template('searchfrom.html')
    response = flask.make_response(html_code)
    return response


#-----------------------------------------------------------------------

@app.route('/searchresults', methods=['GET'])
def searchresults():
    coursenum = ''
    dept = ''
    area = ''
    title = ''

    coursenum = flask.request.args.get('coursenum')
    dept = flask.request.args.get('dept')
    area = flask.request.args.get('area')
    title = flask.request.args.get('title')

    table = handle_overviews(dept, coursenum, area, title)    
    html_code = flask.render_template('searchresults.html', table=table)
    response = flask.make_response(html_code)

        
    return response

def handle_overviews(dept, coursenum, area, title):
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
                (f"%{classid}%", f"%{dept}%", f"%{coursenum}%", \
                    f"%{area}%", f"%{title}%"))
                table = cursor.fetchall()


                #protocol = []
                #for row in table:
                 #   protocol.append(
                  #      {'classid':row[0], 'dept':row[1],
                   #     'coursenum':row[2], 'area':row[3], \
                    #        'title':row[4]})

    except sqlite3.OperationalError as ex:
        protocol = [False, \
            "A server error occurred. " + \
                "Please contact the system administrator."]
        print(f'{sys.argv[0]}: {ex}', file=sys.stderr)
        #send to browser
        except Exception as thing:
            print(f'{sys.argv[0]}: {thing}', file=sys.stderr)

    except Exception as ex:
        print(f'{sys.argv[0]}: {ex}', file=sys.stderr)

    return table



def main():
    try:

        


        

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
