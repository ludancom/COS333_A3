#!/usr/bin/env python

#-----------------------------------------------------------------------
# testregoverviews.py
# Author: Bob Dondero
#-----------------------------------------------------------------------

import os
import sys
import argparse

#-----------------------------------------------------------------------

MAX_LINE_LENGTH = 72
UNDERLINE = '-' * MAX_LINE_LENGTH

#-----------------------------------------------------------------------

def parse_args():

    parser = argparse.ArgumentParser(
        description=
        "Test the Registrar's application's handling of " +
        "class overviews requests")
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

    exec_command(program, prefix + '-d COS')
    exec_command(program, prefix + '-d COS -a qr -n 2 -t intro')

    # Add more tests here.
    exec_command(program, prefix + '-n 333')
    exec_command(program, prefix + '-n b')
    exec_command(program, prefix + '-a Qr')
    exec_command(program, prefix + '-t intro')
    exec_command(program, prefix + '-t science')
    exec_command(program, prefix + '-t C_S')
    exec_command(program, prefix + '-t c%S')
    exec_command(program, prefix + '-d cos -n 3')
    exec_command(program, prefix + '-t "Independent Study"')
    exec_command(program, prefix + '-t "Independent Study "')
    exec_command(program, prefix + '-t "Independent Study  "')
    exec_command(program, prefix + '-t " Independent Study"')
    exec_command(program, prefix + '-t "  Independent Study"')
    exec_command(program, prefix + '-t=-c')

    # Errors
    # Erroneous command-line arguments
    exec_command(program, prefix + 'a qr')
    exec_command(program, prefix + '-A qr')
    exec_command(program, prefix + '"-a " qr')
    exec_command(program, prefix + '-a qr st')
    exec_command(program, prefix + '-a')
    exec_command(program, prefix + '-a qr -d')
    exec_command(program, prefix + '-a -d cos')
    exec_command(program, prefix + '-x')
    # Invalid Port
    exec_command(program, host + ' ' + str(0) + ' ' + '-n 333')
    # Invalid Host 
    # We tried to test the program with an invalid host, but it results in issues with time ([Errno 60] Operation timed out)
    # exec_command(program, "10.47.241.119" + ' ' + str(port) + ' ' + '-n 333')

#-----------------------------------------------------------------------

if __name__ == '__main__':
    main()
