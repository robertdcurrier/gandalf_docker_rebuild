#!/usr/bin/env python3
"""
Author: bob.currier@gcoos.org
Create Date:   2017-03-08
Modified Date:   2020-10-28
Notes: MongoDB routines for HABscope V3 -- we need the user auth code here
so we can authenticate website. We don't need this in pt3, but might leave
in so we don't have two files to track...

pylint: 10.0
"""
import os
import sys
import json
import time
import hashlib
from datetime import datetime
import pymongo as pymongo
from pymongo import MongoClient
from flask_login import current_user


def load_user(email):
    """
    DOCSTRING
    """
    client = connect_mongo()
    db = client.gandalf
    user = db.users.find({'user_email': email})
    return user[0]


def auth_user(id, pw):
    """
    DOCSTRING
    """
    client = connect_mongo()
    db = client.gandalf
    user = db.users.find({'user_email': id.lower()})
    hash = hashlib.md5(pw.encode())
    if hash.hexdigest() == user[0]['user_pw']:
        return True
    else:
        return False


def connect_mongo():
    """
    DOCSTRING
    """
    client = MongoClient('mongo:27017')
    return client

if __name__ == '__main__':
    user = load_user('robertdcurrier@gmail.com')
    print(user)
