#!/usr/bin/env python3
import argparse
import hashlib

def create_pw(pw):
    """
    DOCSTRING
    """
    hash = hashlib.md5(pw.encode())
    return hash


def init_app():
    """
    kick it
    """
    args = get_args()
    hash = create_pw(args['password'])
    print(hash.hexdigest())

def get_args():
    """
    Gets command line args
    """
    arg_p = argparse.ArgumentParser()
    arg_p.add_argument("-p", "--password", required=True,
                       help="Plain-text password")
    args = vars(arg_p.parse_args())
    return args

if __name__ == '__main__':
    init_app()
