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
                (f"%{dept}%", f"%{coursenum}%", f"%{area}%", f"%{title}%"))
                table = cursor.fetchall()
        return table

    except sqlite3.OperationalError as ex:
        protocol = [False, \
            "A server error occurred. " + \
                "Please contact the system administrator."]
        print(f'{sys.argv[0]}: {ex}', file=sys.stderr)
        #send to browser

    except Exception as ex:
        print(f'{sys.argv[0]}: {ex}', file=sys.stderr)

    
#-----------------------------------------------------------------------

def handle_details(classid):
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

                return  {
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
                }

              
    except sqlite3.OperationalError as ex:
        print("A server error occurred. " + \
                "Please contact the system administrator.")
        print(f'{sys.argv[0]}: {ex}', file=sys.stderr)
    except KeyError:
        pass
    except Exception as ex:
        print(f'{sys.argv[0]}: {ex}', file=sys.stderr)


#-----------------------------------------------------------------------
@app.route('/', methods=['GET'])
@app.route('/searchresults', methods=['GET'])
def searchresults():
    coursenum = flask.request.args.get('coursenum', '')
    dept = flask.request.args.get('dept', '')
    area = flask.request.args.get('area', '')
    title = flask.request.args.get('title', '')

    
    table = handle_overviews(dept, coursenum, area, title) 

    
    html_code = flask.render_template('searchresults.html', table=table, dept = dept, coursenum = coursenum, area = area, title=title)
    response = flask.make_response(html_code)

    response.set_cookie('prevdept', dept)
    response.set_cookie('coursenum', coursenum)
    response.set_cookie('prevarea', area)
    response.set_cookie('prevtitle', title)
    
    return response

#-----------------------------------------------------------------------

@app.route('/details', methods =['GET'])
def details():
    dept = flask.request.cookies.get("prevdept", '')
    coursenum = flask.request.cookies.get("coursenum", '')
    areas = flask.request.cookies.get("prevarea", '')
    titles = flask.request.cookies.get("prevtitle", '')

    table = handle_details(flask.request.args.get('classid'))
    html_code = flask.render_template('details.html', 
    classid = table['classid'],
    days=table['days'], 
    starttime=table['starttime'], 
    endtime=table['endtime'], 
    bldg=table['bldg'], 
    room=table['roomnum'], 
    courseid=table['courseid'],
    deptnums=table['deptcoursenums'],
    area=table['area'],
    title=table['title'],
    descrip=table['descrip'],
    prereqs=table['prereqs'],
    profs=table['profnames'],
    dept = dept,
    coursenum = coursenum,
    areas = areas,
    titles = titles
    )

    response = flask.make_response(html_code)
    
    return response

#-----------------------------------------------------------------------

