#!/usr/bin/env python

#-----------------------------------------------------------------------
# testregdetails.py
# Author: Bob Dondero
#-----------------------------------------------------------------------

import os
import sys
import argparse
import shutil

#-----------------------------------------------------------------------

MAX_LINE_LENGTH = 72
UNDERLINE = '-' * MAX_LINE_LENGTH

#-----------------------------------------------------------------------

def parse_args():

    parser = argparse.ArgumentParser(
        description=
        "Test the Registrar's application's handling of " +
        "class details requests")
    parser.add_argument('program', metavar='program', type=str,
        help='the client program to run')
    parser.add_argument('host', metavar='host', type=str,
        help='the host on which the server is running')
    parser.add_argument('port', metavar='port', type=int,
        help='the port at which the server is listening')
    args = parser.parse_args()

    return (args.program, args.host, args.port)

#-----------------------------------------------------------------------

def print_flush(message):
    print(message)
    sys.stdout.flush()

#-----------------------------------------------------------------------

def exec_command(program, args):

    print_flush(UNDERLINE)
    command = 'python ' + program + ' ' + args
    print_flush(command)
    exit_status = os.system(command)
    if os.name == 'nt':  # Running on MS Windows?
        print_flush('Exit status = ' + str(exit_status))
    else:
        print_flush('Exit status = ' + str(os.WEXITSTATUS(exit_status)))

#-----------------------------------------------------------------------

def main():

    program, host, port = parse_args()

    exec_command(program, '-h')

    prefix = host + ' ' + str(port) + ' '

    exec_command(program, prefix + '8321')

    # Add more tests here.
    # Normal Data 
    exec_command(program, prefix + '9032')
    exec_command(program, prefix + '9003')
    exec_command(program, prefix + '9002')
    
    # Unusual Data 
    # Courses with multiple cross-referenced departments/numbers 
    exec_command(program, prefix + '8293')
    exec_command(program, prefix + '10000')
    exec_command(program, prefix + '9007')
    # Courses with long titles
    exec_command(program, prefix + '9977')
    exec_command(program, prefix + '9019')
    # Courses with long descriptions
    exec_command(program, prefix + '10004')
    # Courses with multiple professors
    exec_command(program, prefix + '10006')
    exec_command(program, prefix + '10007')
    exec_command(program, prefix + '9017')
    exec_command(program, prefix + '9018')
    # Courses with no active class
    exec_command(program, prefix + '10008')
    # Courses with no professors
    exec_command(program, prefix + '9012')
    exec_command(program, prefix + '9013')
    exec_command(program, prefix + '10188')
    # Courses with no area 
    exec_command(program, prefix + '10012')

    # Errors
    # Erroneous command-line arguments
    exec_command(program, prefix + '')
    exec_command(program, prefix + '8321 9032')
    exec_command(program, prefix + 'abc123')
    exec_command(program, prefix + '9034')
    # Database cannot be opened
    shutil.copy('reg.sqlite', 'regbackup.sqlite')
    os.remove('reg.sqlite')
    exec_command(program, prefix + '9020')
    shutil.copy('regbackup.sqlite', 'reg.sqlite')
    # Corrupted database
    shutil.copy('regflawed.sqlite', 'reg.sqlite')
    exec_command(program, prefix + '9016') # No Prereqs
    shutil.copy('regbackup.sqlite', 'reg.sqlite')
    # Invalid Port
    exec_command(program, host + ' ' + str(0) + ' ' + '9018')
    # Invalid Host 
    # We tried to test the program with an invalid host, but it results in issues with time ([Errno 60] Operation timed out)
    # exec_command(program, "10.47.241.119" + ' ' + str(port) + ' ' + '9018')

if __name__ == '__main__':
    main()
