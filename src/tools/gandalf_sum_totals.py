#!/usr/bin/env python3
"""
Name:   gandalf_sum_totals.py
Author: robertdcurrier@gmail.com
Created: 2020-06-22
Modified: 2020-06-22
Notes: Parses summaries.json and builds small json summary file
for display on dashboards
"""
DEBUG = False
import json
import pandas as pd


def write_json(summary):
    """
    Name:   write_json
    Author: robertdcurrier@gmail.com
    Created: 2020-06-22
    Modified: 2020-06-22
    Notes: Writes json summary data to outfile
    """
    print("write_json()")
    outfile = ('/data/gandalf/gandalf_configs/'
                 'deployment_summaries/gandalf_sum_totals.json')
    outf = open(outfile, 'w')
    print(summary, file=outf)
    outf.flush()
    outf.close()

def build_summary(json_file):
    """
    Name:   build_summary
    Author: robertdcurrier@gmail.com
    Created: 2020-06-22
    Modified: 2020-06-22
    Notes: Parses summaries.json and builds small json summary file
    for display on dashboards
    """
    print("build_summary()")
    data_frame = pd.read_json(json_file, orient='records')
    deployments = 0
    km = 0
    days = 0

    for idx, row in data_frame.iterrows():
        km = km + row['distance']
        days = days + row['days_wet']
    if DEBUG:
        print('Deployments: %d' % idx)
        print('Kilometers: %d' % km)
        print('Days Wet: %d' % days)

    summary = json.dumps({"deployments" : idx, "km" : km, "days_wet" : days})
    write_json(summary)

if __name__ == '__main__':
    json_file = ('/data/gandalf/gandalf_configs/'
                 'deployment_summaries/summaries.json')
    build_summary(json_file)
