#!/usr/bin/env python3
"""
Created:        2019-10-09
Modified:       2019-10-09
Author:         robertdcurrier@gmail.com
Notes:          This app harvests data from Slocum dockservers
or their proxy using rsync or wget methods. If we have an account
on the dockserver we use rsync, if not, it's wget. This app used
to be a shell script. We are migrating to pure Python to better
integrate into the GANDALF architecture. The app will be called
from gandalf_mcp. There will be corresponding gandalf_harvest_waveglider
and gandalf_harvest_navocean modules.
"""
import os
import sys
from subprocess import Popen, PIPE
from gandalf_utils import get_vehicle_config
from gandalf_utils import get_deployed_slocum
from gandalf_utils import get_deployment_status_all


def use_wget(vehicle, v_config):
    """
    gets logs, sbd and tbd files using
    """
    # settings
    debug = bool(v_config['gandalf']['debug'])
    dockserver = v_config['gandalf']['dockserver']
    dockuser = v_config['gandalf']['dockuser']
    docklogpath = v_config['gandalf']['docklogpath']
    dockfrompath = v_config['gandalf']['dockfrompath']
    docklogfilter = v_config['gandalf']['docklogfilter']
    dockfromfilter = v_config['gandalf']['dockfromfilter']
    logdir = '%s/ascii_files/logs' % v_config['gandalf']['deployed_data_dir']
    sbddir = '%s/binary_files/sbd' % v_config['gandalf']['deployed_data_dir']
    tbddir = '%s/binary_files/tbd' % v_config['gandalf']['deployed_data_dir']

    # logs
    print("use_wget(%s): Fetching logs" % vehicle)
    os.chdir(logdir)
    the_command = ("wget -v -r -l1 -nH --cut-dirs=3 %s/%s -A '%s.log'" %
          (dockserver, docklogpath, docklogfilter))
    if debug:
        print(the_command)
    the_pipe = Popen(the_command, shell=True, stdin=PIPE, stderr=PIPE)
    Popen.communicate(the_pipe)

    # sbd
    print("use_wget(%s): Fetching sbd files" % vehicle)
    os.chdir(sbddir)
    the_command = ("wget -v -r -l1 -nH --cut-dirs=3 %s/%s -A '%s.sbd'" %
          (dockserver, dockfrompath, dockfromfilter))
    if debug:
        print(the_command)
    the_pipe = Popen(the_command, shell=True, stdin=PIPE, stderr=PIPE)
    Popen.communicate(the_pipe)

    # tbd
    print("use_wget(%s): Fetching tbd files" % vehicle)
    os.chdir(tbddir)
    the_command = ("wget -v -r -l1 -nH --cut-dirs=3 %s/%s -A '%s.tbd'" %
          (dockserver, dockfrompath, dockfromfilter))
    if debug:
        print(the_command)
    the_pipe = Popen(the_command, shell=True, stdin=PIPE, stderr=PIPE)
    Popen.communicate(the_pipe)



def use_rsync(vehicle, v_config):
    """
    gets logs, sbd and tbd files using subprocess
    """
    # settings
    debug = bool(v_config['gandalf']['debug'])
    operator = v_config['gandalf']['operator'].lower()
    dockserver = v_config['gandalf']['dockserver']
    dockuser = v_config['gandalf']['dockuser']
    docklogpath = v_config['gandalf']['docklogpath']
    dockfrompath = v_config['gandalf']['dockfrompath']
    logdir = '%s/ascii_files/logs' % v_config['gandalf']['deployed_data_dir']
    sbddir = '%s/binary_files/sbd' % v_config['gandalf']['deployed_data_dir']
    tbddir = '%s/binary_files/tbd' % v_config['gandalf']['deployed_data_dir']

    # logs
    print("use_rsync(%s): Fetching logs" % vehicle)
    the_command = ("rsync -avp %s@%s:%s/*.log %s" %
          (dockuser, dockserver, docklogpath, logdir))
    if debug:
        print(the_command)
    the_pipe = Popen(the_command, shell=True, stdin=PIPE, stderr=PIPE)
    Popen.communicate(the_pipe)

    # sbd
    print("use_rsync(%s): Fetching sbd files" % vehicle)
    the_command = ("rsync -avp %s@%s:%s/[a-zA-Z]*.sbd %s" %
          (dockuser, dockserver, dockfrompath, sbddir))
    if debug:
        print(the_command)
    the_pipe = Popen(the_command, shell=True, stdin=PIPE, stderr=PIPE)
    Popen.communicate(the_pipe)

    # tbd
    print("use_rsync(%s): Fetching tbd files" % vehicle)
    the_command = ("rsync -avp %s@%s:%s/[a-zA-Z]*.tbd %s" %
          (dockuser, dockserver, dockfrompath, tbddir))
    if debug:
        print(the_command)
    the_pipe = Popen(the_command, shell=True, stdin=PIPE, stderr=PIPE)
    Popen.communicate(the_pipe)



def harvest_slocum(vehicle):
    """
    Uses wget or rsync to pull down latest files
    """
    print("harvest_local(%s)" % vehicle)
    v_config = get_vehicle_config(vehicle)
    if v_config['gandalf']['harvest_method'] == 'rsync':
        use_rsync(vehicle, v_config)
    if v_config['gandalf']['harvest_method'] == 'wget':
        use_wget(vehicle, v_config)


def harvest():
    """
    what you sow, so shall you reap
    """
    deployed = get_deployment_status_all()
    slocum_gliders = get_deployed_slocum(deployed)
    for vehicle in slocum_gliders:
        harvest_slocum(vehicle)


if __name__ == '__main__':
    harvest()

