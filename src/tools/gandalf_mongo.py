#!/usr/bin/env python3
"""
Author: bob.currier@gcoos.org
Create Date:   2017-03-08
Modified Date:   2022-04-27
Notes: MongoDB routines for HABscope V2 -- we need the user auth code here
so we can authenticate website. We don't need this in pt3, but might leave
in so we don't have two files to track...

"""
import os
import sys
import json
import time
import hashlib
import collections
from datetime import datetime
import pymongo as pymongo
from pymongo import MongoClient
from flask_login import current_user


def load_user(email):
    """
    DOCSTRING
    """
    client = connect_mongo()
    db = client.habscope2
    user = db.users.find({'user_email': email})
    return user


def auth_user(id, pw):
    """
    DOCSTRING
    """
    client = connect_mongo()
    db = client.habscope2
    try:
        user = db.users.find({'user_email': id.lower()})[0]
    except IndexError:
        return False
    hash = hashlib.md5(pw.encode())
    if hash.hexdigest() == user['user_pw']:
        return True
    else:
        return False


def connect_mongo():
    """
    DOCSTRING
    """
    client = MongoClient('mongo:27017')
    return client


def fetch_record(id):
    """
    gets a single active record
    """
    client = connect_mongo()
    db = client.habscope2
    results = db.imageLogs.find({"_id": id})
    for record in results:
        return(record)


def fetch_records(taxa):
    """
    gets all records for given taxa
    """
    client = connect_mongo()
    db = client.habscope2
    the_records = []
    if taxa == 'all':
        results = db.imageLogs.find().sort("recorded_ts", pymongo.DESCENDING)
    else:
        results = db.imageLogs.find({"taxa" : taxa}).sort("recorded_ts",
                                                          pymongo.DESCENDING)

    for result in results:
        recorded_ts = result['recorded_ts']
        recorded_ts = (datetime.utcfromtimestamp(
            recorded_ts).strftime('%Y-%m-%d %H:%M:%S'))
        result['recorded_ts'] = recorded_ts
        processed_ts = result['processed_ts']
        processed_ts = (datetime.utcfromtimestamp(
            processed_ts).strftime('%Y-%m-%d %H:%M:%S'))
        result['processed_ts'] = processed_ts
        the_records.append(result)
    return the_records


def insert_record(record_json):
    """
    DOCSTRING
    """

    client = connect_mongo()
    db = client.habscope2
    result = db.imageLogs.insert_one(record_json)


if __name__ == '__main__':
    # For command line usage
    print(auth_user('sdavis@leegov.com','habsc0p3'))
    print(fetch_deleted())
