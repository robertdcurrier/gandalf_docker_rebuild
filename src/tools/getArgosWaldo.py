#!/usr/bin/env python3
import sys
import telnetlib
import getpass
import string
import os
from time import *
import datetime
import re

def dinkumConvert(gpsLon,gpsLat):
    gpsLon = float(gpsLon)
    gpsLat = float(gpsLat)
    latInt = int((gpsLat / 100.0))
    lonInt = int((gpsLon / 100.0))
    lat = (latInt + (gpsLat - (latInt * 100)) / 60.0)
    lon = (lonInt + (gpsLon - (lonInt * 100)) / 60.0)
    lat = eval("%0.4f" % (lat))
    lon = eval("%0.4f" % (lon))
    return lon,lat
    if DEBUG > 0:
        print("Converted %0.4f %0.4f to %0.4f %0.4f" % (gpsLon,gpsLat,lon,lat))


def getArgos():

 #Waldo setup
    argosPTT = "64018"
    #argosHost = "datadist.argosinc.com"
    argosHost = "ArgosServer.cls.fr"
    argosUser = "MOTELAB\n"
    argosPass = "ECOTOX\n"
    argosCommand = "COM,3215,PHYT,64018\n"

    session = telnetlib.Telnet(argosHost)
    session.read_until("Username:")
    session.write(argosUser)
    session.read_until("Password:")
    session.write(argosPass)
    session.write(argosCommand)
    session.write("lo\n")
    myBuffer = session.read_all()

    messageBlock = myBuffer[160:620]
    myMatch = myBuffer.find(argosPTT)
    if (myMatch != -1):
        julianToday = strftime("%j",localtime())
        argosLat = myBuffer[102:108]
        argosLon = myBuffer[111:117]
        argosCollectDate = myBuffer[134:137]
        argosCollectTime = myBuffer[138:142]
        argosLocationTime = myBuffer[148:152]
        argosLocationDate = myBuffer[144:147]
        julianToday = int(julianToday)
        argosCollectDate = int(argosCollectDate)
        argosLocationDate = int(argosLocationDate)
        argosCollectAge = (julianToday - argosCollectDate)
        argosLocationAge = (julianToday - argosLocationDate)

        if(argosCollectAge == 0):
            currentDate = datetime.date.today()
            print("ARGOS data collected at %s UTC on %s" % (argosCollectTime,currentDate))
        else:
            currentDate = datetime.date.today()
            argosDifference = datetime.timedelta(days=-argosCollectAge)
            print("Data Collected: %s" % (currentDate + argosDifference))
        return messageBlock

def parseMessageBlock(messageBlock):

    gotData = 0
    command = ("cat - | /opt/dinkum/prntargo_rev1")
    i,o = os.popen2(command)
    i.write(messageBlock)
    i.close()
    myBuffer = o.readlines()
    o.close()
    for line in myBuffer:
        if(line.find('<none>') <= 0):
            if line.startswith("Curr Valid Fix"):
                gotData = 1
                gliderLat = line[20:29]
                gliderLon = line[31:39]
                (lon,lat) = dinkumConvert(gliderLon,gliderLat)

    if gotData == 1:
        print("Last reported glider position: %.4f %.4f" % (lat,lon))
    else:
        print("Valid message block not received...")

def Main():
    messageBlock = getArgos()
    parseMessageBlock(messageBlock)

gps = dinkumConvert(2708.762, -8225.484)
print(gps)
