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

def escape(s):
    s = s.replace('\\', '\\\\')  # escape backslash first
    s = s.replace('%', '\\%')
    s = s.replace('_', '\\_')
    return s

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
                    AND dept LIKE ? ESCAPE \\
                    AND coursenum LIKE ? ESCAPE \\
                    AND area LIKE ? ESCAPE \\
                    AND title LIKE ? ESCAPE \\
                    ORDER BY crosslistings.dept, crosslistings.coursenum, classes.classid
                    '''
                cursor.execute(statement_str,
                (f"%{escape(dept)}%", f"%{escape(coursenum)}%", f"%{escape(area)}%", f"%{escape(title)}%"))
                table = cursor.fetchall()
        return table

    except sqlite3.OperationalError as ex:
        print(f'{sys.argv[0]}: {ex}', file=sys.stderr)
        return [False, \
            "A server error occurred. " + \
                "Please contact the system administrator."]
    
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
                int(classid)
                if len(classdeets) == 0:
                    table = [False, \
                        "no class with classid "+str(classid)+" exists"]
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

                return  [True, {
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

              
    except sqlite3.OperationalError as ex:
        print(f'{sys.argv[0]}: {ex}', file=sys.stderr)
        return [False, "A server error occurred. " + \
                "Please contact the system administrator."]
    except KeyError:
        return table
    except ValueError as ex:
        return(False, "non-integer classid: classid must be an integer value")
    except Exception as ex:
        return(False, str(sys.argv[0]) + ": " + str(ex))


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

    response.set_cookie('prevdept', encode_url(dept))
    response.set_cookie('coursenum', encode_url(coursenum))
    response.set_cookie('prevarea', encode_url(area))
    response.set_cookie('prevtitle', encode_url(title))
    
    return response

#-----------------------------------------------------------------------

@app.route('/regdetails', methods =['GET'])
def regdetails():
    dept = decode_url(flask.request.cookies.get("prevdept", ''))
    coursenum = decode_url(flask.request.cookies.get("coursenum", ''))
    areas = decode_url(flask.request.cookies.get("prevarea", ''))
    titles = decode_url(flask.request.cookies.get("prevtitle", ''))

    table = handle_details(flask.request.args.get('classid'))

    if table[0] == False:
        return flask.redirect(flask.url_for("error", classid=flask.request.args.get('classid')))


    html_code = flask.render_template('regdetails.html', 
    classid = table[1]['classid'],
    days=table[1]['days'], 
    starttime=table[1]['starttime'], 
    endtime=table[1]['endtime'], 
    bldg=table[1]['bldg'], 
    room=table[1]['roomnum'], 
    courseid=table[1]['courseid'],
    deptnums=table[1]['deptcoursenums'],
    area=table[1]['area'],
    title=table[1]['title'],
    descrip=table[1]['descrip'],
    prereqs=table[1]['prereqs'],
    profs=table[1]['profnames'],
    dept = dept,
    coursenum = coursenum,
    areas = areas,
    titles = titles,
    )

    response = flask.make_response(html_code)
    
    return response

#-----------------------------------------------------------------------

@app.route('/error', methods =['GET'])
def error():
    table = handle_details(flask.request.args.get('classid'))
    html_code = flask.render_template('error.html', error=table[1])
    response = flask.make_response(html_code)
    
    return response

#-----------------------------------------------------------------------
def encode_url(s):
    return s.replace(' ', '+')
#-----------------------------------------------------------------------
def decode_url(s):
    return s.replace('+', ' ')
