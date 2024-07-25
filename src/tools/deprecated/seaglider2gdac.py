#!/usr/bin/python
""" Script to convert Seaglider nc files into IOOS DAC nc files. IOOS DAC
nc files contain all the temperature and salinity data and relevant
metadata (including QC flags) contained in the Seaglider nc files,
excluding other information such as piloting or vehicle engineering parameters.

In this version, for gliders with gpctd the pressure is calculated from
density and latitude, using CSIRO's Seawater Matlab package procedure
"""


# Francis Bringas, 2018Aug17
# 		2018Aug17: first version based on /data/bringas/TSG/CODES/ascii2nc
#(Perl) from 2018Jun28.
#Kevin Martin, 13Sept2019
#		Edited for USM use in the GoMex for 636



__author__ = "Kevin Martin"



from sys import argv as argv
import os
import time as tm
from netCDF4 import Dataset
from netCDF4 import stringtochar
import numpy


file_in = argv[1]				# input Seaglider nc file. For example: ./p5470023.nc
dir_out = argv[2]				# directory to save output IOOS nc files. For example: ./nc2IOOS
sgid ='601'					# glider call sign. For example, for SG547: 547
#cmission = argv[4]				# mission name. For example: M05JUL2016
dir_out_nc2IOOS = argv[3]		# output directory for log file. For example: ./nc2IOOS (we use the same as dir_out, but it could be different)

#===================== --- Writing IOOS file_out --- ===================
def write_file_out(out_type):
    # ---- defining variables -----
    conventions_global = "CF-1.6"
    Metadata_Conventions_global = "CF-1.6, Unidata Dataset Discovery v1.0"
    acknowledgment_global = "This project is funded by Shell Exploration & Production Company"
    comment_global = "Underwater glider temperature and salinity profiles"
    contributor_name_global = "Stephan Howden, Kevin Martin, Dawn Petraitis"
    contributor_role_global = "Principal Investigator, Data Manager, Data Manager"
    creator_email_global = "Kevin.m.martin-at-usm.edu"
    creator_name_global = "Kevin Martin"
    creator_url_global = ""
    date_issued_global, date_modified_global = ("",) * 2
    format_version_global = "AOML_Glider_NetCDF_v2.0.nc"
    history_global, title_global = ("",) * 2
    institution_global = "National Oceanic and Atmospheric Administration (NOAA) / National Data Buoy Center (NDBC), University of Southern Mississippi/ School of Ocean Science and Engineering, Shell Exploration & Production Company and Gulf of Mexico Ocean Observing System (GCOOS)"
    keywords_global = "AUVS > Autonomous Underwater Vehicles, Oceans > Ocean Pressure > Water Pressure, Oceans > Ocean Temperature > Water Temperature, Oceans > Salinity/Density > Conductivity, Oceans > Salinity/Density > Density, Oceans > Salinity/Density > Salinity"
    keywords_vocabulary_global = "GCMD Science Keywords"
    license_global = "These data may be redistributed and used without restrictions. Data provided as is with no expressed or implied warranty of quality control or quality assurance"
    naming_authority_global = ""
    platform_type_global = "Seaglider"
    processing_level_global = "Data provided as is with no expressed or implied assurance of quality assurance or quality control."
    project_global = "Sustained Underwater Glider Observations for Improving Atlantic Tropical Cyclone Intensity Forecasts"
    publisher_email_global = "Kevin.m.martin-at-usm.edu"
    publisher_name_global = "Kevin Martin"
    publisher_url_global = ""
    references_global = ""
    source_global = "Observational data from a profiling underwater glider"
    standard_name_vocabulary_global = "CF-v25"
    summary_global = "Underwater glider data gathered by the National Oceanic and Atmospheric Administration (NOAA)"
    qc_val = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    title_global = id_global
    date_issued_global = tm.strftime("%Y-%m-%dT%H:%M:%SZ", tm.gmtime())     # set as YYYY-mm-ddTHH:MM:SSZ
    date_modified_global = date_issued_global
    history_global = "Created on " + date_issued_global + " using SGnc2IOOSncUSM601_2020_py"
    platform = 0
    instrument_ctd = "SBE41"

    if out_type == "dn":
        dim_time = ndn
        Time = time_dn
        lat = lat_dn
        lon = lon_dn
        pressure = pressure_dn
        depth = depth_dn
        temperature = temperature_dn
        conductivity = conductivity_dn
        salinity = salinity_dn
        density = density_dn
        profile = profile_dn
        profile_time = profile_time_dn
        profile_lat = profile_lat_dn
        profile_lon = profile_lon_dn
        time_uv = time_uv_dn
        lat_uv = lat_uv_dn
        lon_uv = lon_uv_dn
        u = u_dn
        v = v_dn
        time_qc = time_qc_dn
        lat_qc = lat_qc_dn
        lon_qc = lon_qc_dn
        pressure_qc = pressure_qc_dn
        depth_qc = depth_qc_dn
        temperature_qc = temperature_qc_dn
        conductivity_qc = conductivity_qc_dn
        salinity_qc = salinity_qc_dn
        density_qc = density_qc_dn
        profile_time_qc = profile_time_qc_dn
        profile_lat_qc = profile_lat_qc_dn
        profile_lon_qc = profile_lon_qc_dn
        time_uv_qc = time_uv_qc_dn
        lat_uv_qc = lat_uv_qc_dn
        lon_uv_qc = lon_uv_qc_dn
        u_qc = u_qc_dn
        v_qc = v_qc_dn
    else:
        dim_time = nup - ndn
        Time = time_up
        lat = lat_up
        lon = lon_up
        pressure = pressure_up
        depth = depth_up
        temperature = temperature_up
        conductivity = conductivity_up
        salinity = salinity_up
        density = density_up
        profile = profile_up
        profile_time = profile_time_up
        profile_lat = profile_lat_up
        profile_lon = profile_lon_up
        time_uv = time_uv_up
        lat_uv = lat_uv_up
        lon_uv = lon_uv_up
        u = u_up
        v = v_up
        time_qc = time_qc_up
        lat_qc = lat_qc_up
        lon_qc = lon_qc_up
        pressure_qc = pressure_qc_up
        depth_qc = depth_qc_up
        temperature_qc = temperature_qc_up
        conductivity_qc = conductivity_qc_up
        salinity_qc = salinity_qc_up
        density_qc = density_qc_up
        profile_time_qc = profile_time_qc_up
        profile_lat_qc = profile_lat_qc_up
        profile_lon_qc = profile_lon_qc_up
        time_uv_qc = time_uv_qc_up
        lat_uv_qc = lat_uv_qc_up
        lon_uv_qc = lon_uv_qc_up
        u_qc = u_qc_up
        v_qc = v_qc_up

    ymd = tm.strftime("%Y%m%d", tm.gmtime(Time[0]))
    hms = tm.strftime("%H%M%S", tm.gmtime(Time[0]))
    fo_name = sgname + "_" + ymd + "T" + hms + "_delayed.nc"  # Example:  SG609_20140913T000049_delayed.nc
    fo = dir_out + "/" + fo_name


    # --- create file_out ---
    dataset = Dataset(fo, "w", format = "NETCDF4_CLASSIC")

    # ---- Define record dimension: ----
    time = dataset.createDimension("time", dim_time)
    traj_strlen = dataset.createDimension("traj_strlen", 16)
    string_5 = dataset.createDimension("string_5", 5)

    # --- define variables ---
    trajectoryS = dataset.createVariable("trajectory", "S1", ("traj_strlen",))
    trajectoryS.cf_role = "trajectory_id"
    trajectoryS.comment = "A trajectory is a single deployment of a glider and may span multiple data files."
    trajectoryS.long_name = "Trajectory/Deployment Name"
    trajectoryS[:] = stringtochar(numpy.array([trajectory], 'S16'))

    TimeS = dataset.createVariable("time", "f8", ("time",), fill_value = float('nan'))
    TimeS.ancillary_variables = "time_qc"
    TimeS.calendar = "gregorian"
    TimeS.long_name = "Time"
    TimeS.observation_type = "measured"
    TimeS.standard_name = "time"
    TimeS.units = "seconds since 1970-01-01T00:00:00Z"
    TimeS[:] = Time

    latS = dataset.createVariable("lat", "f8", ("time",), fill_value = float('nan'))
    latS.ancillary_variables = "lat_qc"
    latS.comment = "Values may be interpolated between measured GPS fixes"
    latS.coordinate_reference_frame = "urn:ogc:crs:EPSG::4326"
    latS.long_name = "Latitude"
    latS.observation_type = "measured"
    latS.platform = "glider"
    latS.reference = "WGS84"
    latS.standard_name = "latitude"
    latS.units = "degrees_north"
    latS.valid_min = -90.
    latS.valid_max = 90.
    latS[:] = lat

    lonS = dataset.createVariable("lon", "f8", ("time",), fill_value = float('nan'))
    lonS.ancillary_variables = "lon_qc"
    lonS.comment = "Values may be interpolated between measured GPS fixes"
    lonS.coordinate_reference_frame = "urn:ogc:crs:EPSG::4326"
    lonS.long_name = "Longitude"
    lonS.observation_type = "measured"
    lonS.platform = "glider"
    lonS.reference = "WGS84"
    lonS.standard_name = "longitude"
    lonS.units = "degrees_east"
    lonS.valid_min = -180.
    lonS.valid_max = 180.
    lonS[:] = lon

    pressureS = dataset.createVariable("pressure", "f8", ("time",), fill_value = float('nan'))
    pressureS.accuracy = " "
    pressureS.ancillary_variables = "pressure_qc"
    pressureS.comment = "Uncorrected sea-water pressure"
    pressureS.instrument = "instrument_ctd"
    pressureS.long_name = "Pressure"
    pressureS.observation_type = "measured"
    pressureS.platform = "glider"
    pressureS.positive = "down"
    pressureS.precision = " "
    pressureS.reference_datum = "sea-surface"
    pressureS.resolution = " "
    pressureS.standard_name = "sea_water_pressure"
    pressureS.units = "dbar"
    pressureS.valid_min = 0.
    pressureS.valid_max = 2000.
    pressureS[:] = pressure

    depthS = dataset.createVariable("depth", "f8", ("time",), fill_value = float('nan'))
    depthS.accuracy = " "
    depthS.ancillary_variables = "depth_qc"
    depthS.comment = "Depth below the surface, corrected for average latitude"
    depthS.instrument = "instrument_ctd"
    depthS.long_name = "Depth"
    depthS.observation_type = "calculated"
    depthS.platform = "glider"
    depthS.positive = "down"
    depthS.precision = " "
    depthS.reference_datum = "sea-surface"
    depthS.resolution = " "
    depthS.standard_name = "depth"
    depthS.units = "m"
    depthS.valid_min = 0.
    depthS.valid_max = 2000.
    depthS[:] = depth

    temperatureS = dataset.createVariable("temperature", "f8", ("time",), fill_value = float('nan'))
    temperatureS.accuracy = " "
    temperatureS.ancillary_variables = "temperature_qc"
    temperatureS.comment = "Temperature (in situ) corrected for thermistor first-order lag"
    temperatureS.instrument = "instrument_ctd"
    temperatureS.long_name = "Temperature"
    temperatureS.observation_type = "measured"
    temperatureS.platform = "glider"
    temperatureS.precision = " "
    temperatureS.resolution = " "
    temperatureS.standard_name = "sea_water_temperature"
    temperatureS.units = "Celsius"
    temperatureS.valid_min = -5.
    temperatureS.valid_max = 40.
    temperatureS[:] = temperature

    conductivityS = dataset.createVariable("conductivity", "f8", ("time",), fill_value = float('nan'))
    conductivityS.accuracy = " "
    conductivityS.ancillary_variables = "conductivity_qc"
    conductivityS.comment = "Conductivity corrected for anomalies"
    conductivityS.instrument = "instrument_ctd"
    conductivityS.long_name = "Conductivity"
    conductivityS.observation_type = "measured"
    conductivityS.platform = "glider"
    conductivityS.precision = " "
    conductivityS.resolution = " "
    conductivityS.standard_name = "sea_water_electrical_conductivity"
    conductivityS.units = "S m-1"
    conductivityS.valid_min = 0.
    conductivityS.valid_max = 10.
    conductivityS[:] = conductivity

    salinityS = dataset.createVariable("salinity", "f8", ("time",), fill_value = float('nan'))
    salinityS.accuracy = " "
    salinityS.ancillary_variables = "salinity_qc"
    salinityS.comment = "Salinity corrected for thermal-inertia effects (PSU)"
    salinityS.instrument = "instrument_ctd"
    salinityS.long_name = "Salinity"
    salinityS.observation_type = "calculated"
    salinityS.platform = "glider"
    salinityS.precision = " "
    salinityS.resolution = " "
    salinityS.standard_name = "sea_water_practical_salinity"
    salinityS.units = "1e-3"
    salinityS.valid_min = 0.
    salinityS.valid_max = 40.
    salinityS[:] = salinity

    densityS = dataset.createVariable("density", "f8", ("time",), fill_value = float('nan'))
    densityS.accuracy = " "
    densityS.ancillary_variables = "density_qc"
    densityS.comment = "Sea water potential density"
    densityS.instrument = "instrument_ctd"
    densityS.long_name = "Density"
    densityS.observation_type = "calculated"
    densityS.platform = "glider"
    densityS.precision = " "
    densityS.resolution = " "
    densityS.standard_name = "sea_water_density"
    densityS.units = "kg m-3"
    densityS.valid_min = 1015.
    densityS.valid_max = 1040.
    densityS[:] = density

    profile_idS = dataset.createVariable("profile_id", "i4", fill_value = -999)
    profile_idS.comment = "Sequential profile number within the trajectory. This value is unique in each file that is part of a single trajectory/deployment."
    profile_idS.long_name = "Profile ID"
    profile_idS.valid_min = 1
    profile_idS.valid_max = 2147483647
    profile_idS[:] = profile

    profile_timeS = dataset.createVariable("profile_time", "f8", fill_value = float('nan'))
    profile_timeS.calendar = "gregorian"
    profile_timeS.comment = "Timestamp corresponding to the mid-point of the profile"
    profile_timeS.long_name = "Profile Center Time"
    profile_timeS.observation_type = "calculated"
    profile_timeS.platform = "glider"
    profile_timeS.standard_name = "time"
    profile_timeS.units = "seconds since 1970-01-01T00:00:00Z"
    profile_timeS[:] = profile_time

    profile_latS = dataset.createVariable("profile_lat", "f8", fill_value = float('nan'))
    profile_latS.comment = "Value is interpolated to provide an estimate of the latitude at the mid-point of the profile"
    profile_latS.long_name = "Profile Center Latitude"
    profile_latS.observation_type = "calculated"
    profile_latS.platform = "glider"
    profile_latS.standard_name = "latitude"
    profile_latS.units = "degrees_north"
    profile_latS.valid_min = -90.
    profile_latS.valid_max = 90.
    profile_latS[:] = profile_lat

    profile_lonS = dataset.createVariable("profile_lon", "f8", fill_value = float('nan'))
    profile_lonS.comment = "Value is interpolated to provide an estimate of the longitude at the mid-point of the profile"
    profile_lonS.long_name = "Profile Center Longitude"
    profile_lonS.observation_type = "calculated"
    profile_lonS.platform = "glider"
    profile_lonS.standard_name = "longitude"
    profile_lonS.units = "degrees_east"
    profile_lonS.valid_min = -180.
    profile_lonS.valid_max = 180.
    profile_lonS[:] = profile_lon

    time_uvS = dataset.createVariable("time_uv", "f8", fill_value = float('nan'))
    time_uvS.calendar = "gregorian"
    time_uvS.comment = "The depth-averaged current is an estimate of the net current measured while the glider is underwater. The value is calculated over the entire underwater segment, which may consist of 1 or more dives."
    time_uvS.long_name = "Depth-Averaged Time"
    time_uvS.observation_type = "calculated"
    time_uvS.standard_name = "time"
    time_uvS.units = "seconds since 1970-01-01T00:00:00Z"
    time_uvS[:] = time_uv

    lat_uvS = dataset.createVariable("lat_uv", "f8", fill_value = float('nan'))
    lat_uvS.comment = "The depth-averaged current is an estimate of the net current measured while the glider is underwater. The value is calculated over the entire underwater segment, which may consist of 1 or more dives."
    lat_uvS.long_name = "Depth-Averaged Latitude"
    lat_uvS.observation_type = "calculated"
    lat_uvS.platform = "glider"
    lat_uvS.standard_name = "latitude"
    lat_uvS.units = "degrees_north"
    lat_uvS.valid_min = -90.
    lat_uvS.valid_max = 90.
    lat_uvS[:] = lat_uv

    lon_uvS = dataset.createVariable("lon_uv", "f8", fill_value = float('nan'))
    lon_uvS.comment = "The depth-averaged current is an estimate of the net current measured while the glider is underwater. The value is calculated over the entire underwater segment, which may consist of 1 or more dives."
    lon_uvS.long_name = "Depth-Averaged Longitude"
    lon_uvS.observation_type = "calculated"
    lon_uvS.platform = "glider"
    lon_uvS.standard_name = "longitude"
    lon_uvS.units = "degrees_east"
    lon_uvS.valid_min = -180.
    lon_uvS.valid_max = 180.
    lon_uvS[:] = lon_uv

    uS = dataset.createVariable("u", "f8", fill_value = float('nan'))
    uS.comment = "The depth-averaged current is an estimate of the net current measured while the glider is underwater. The value is calculated over the entire underwater segment, which may consist of 1 or more dives."
    uS.long_name = "Depth-Averaged Eastward Sea Water Velocity"
    uS.observation_type = "calculated"
    uS.platform = "glider"
    uS.standard_name = "eastward_sea_water_velocity"
    uS.units = "m s-1"
    uS.valid_min = -10.
    uS.valid_max = 10.
    uS[:] = u

    vS = dataset.createVariable("v", "f8", fill_value = float('nan'))
    vS.comment = "The depth-averaged current is an estimate of the net current measured while the glider is underwater. The value is calculated over the entire underwater segment, which may consist of 1 or more dives."
    vS.long_name = "Depth-Averaged Northward Sea Water Velocity"
    vS.observation_type = "calculated"
    vS.platform = "glider"
    vS.standard_name = "northward_sea_water_velocity"
    vS.units = "m s-1"
    vS.valid_min = -10.
    vS.valid_max = 10.
    vS[:] = v

    platformS = dataset.createVariable("platform", "i4", fill_value = -999)
    platformS.comment = "Seaglider " + sgname
    platformS.id = sgname
    platformS.instrument = "instrument_ctd"
    platformS.long_name = "USM Seaglider " + sgname
    platformS.type = "glider"
    platformS.wmo_id = sgwmo
    platformS[:] = platform

    instrument_ctdS = dataset.createVariable("instrument_ctd", "S1", ("string_5",))
    instrument_ctdS.calibration_date = ctd_calib_date
    instrument_ctdS.calibration_report = " "
    instrument_ctdS.factory_calibrated = " "
    instrument_ctdS.comment = "CTD"
    instrument_ctdS.long_name = "Underway Thermosalinograph"
    instrument_ctdS.make_model = "Seabird SBE41"
    instrument_ctdS.serial_number = ctd_serial_number
    instrument_ctdS.platform = "glider"
    instrument_ctdS.type = "thermosalinograph"
    instrument_ctdS[:] = stringtochar(numpy.array([instrument_ctd], 'S5'))

    time_qcS = dataset.createVariable("time_qc", "i1", ("time",), fill_value = -127)
    time_qcS.flag_meanings = "no_qc_performed good_data probably_good_data bad_data_that_are_potentially_correctable bad_data value_changed not_used not_used interpolated_value missing_value"
    time_qcS.flag_values = qc_val
    time_qcS.long_name = "time Quality Flag"
    time_qcS.standard_name = "time status_flag"
    time_qcS.valid_min = 0
    time_qcS.valid_max = 9
    time_qcS[:] = time_qc

    lat_qcS = dataset.createVariable("lat_qc", "i1", ("time",), fill_value = -127)
    lat_qcS.flag_meanings = "no_qc_performed good_data probably_good_data bad_data_that_are_potentially_correctable bad_data value_changed not_used not_used interpolated_value missing_value"
    lat_qcS.flag_values = qc_val
    lat_qcS.long_name = "latitude Quality Flag"
    lat_qcS.standard_name = "latitude status_flag"
    lat_qcS.valid_min = 0
    lat_qcS.valid_max = 9
    lat_qcS[:] = lat_qc

    lon_qcS = dataset.createVariable("lon_qc", "i1", ("time",), fill_value = -127)
    lon_qcS.flag_meanings = "no_qc_performed good_data probably_good_data bad_data_that_are_potentially_correctable bad_data value_changed not_used not_used interpolated_value missing_value"
    lon_qcS.flag_values = qc_val
    lon_qcS.long_name = "longitude Quality Flag"
    lon_qcS.standard_name = "longitude status_flag"
    lon_qcS.valid_min = 0
    lon_qcS.valid_max = 9
    lon_qcS[:] = lon_qc

    pressure_qcS = dataset.createVariable("pressure_qc", "i1", ("time",), fill_value = -127)
    pressure_qcS.flag_meanings = "no_qc_performed good_data probably_good_data bad_data_that_are_potentially_correctable bad_data value_changed not_used not_used interpolated_value missing_value"
    pressure_qcS.flag_values = qc_val
    pressure_qcS.long_name = "pressure Quality Flag"
    pressure_qcS.standard_name = "sea_water_pressure status_flag"
    pressure_qcS.valid_min = 0
    pressure_qcS.valid_max = 9
    pressure_qcS[:] = pressure_qc

    depth_qcS = dataset.createVariable("depth_qc", "i1", ("time",), fill_value = -127)
    depth_qcS.flag_meanings = "no_qc_performed good_data probably_good_data bad_data_that_are_potentially_correctable bad_data value_changed not_used not_used interpolated_value missing_value"
    depth_qcS.flag_values = qc_val
    depth_qcS.long_name = "depth Quality Flag"
    depth_qcS.standard_name = "depth status_flag"
    depth_qcS.valid_min = 0
    depth_qcS.valid_max = 9
    depth_qcS[:] = depth_qc

    temperature_qcS = dataset.createVariable("temperature_qc", "i1", ("time",), fill_value = -127)
    temperature_qcS.flag_meanings = "no_qc_performed good_data probably_good_data bad_data_that_are_potentially_correctable bad_data value_changed not_used not_used interpolated_value missing_value"
    temperature_qcS.flag_values = qc_val
    temperature_qcS.long_name = "temperature Quality Flag"
    temperature_qcS.standard_name = "sea_water_temperature status_flag"
    temperature_qcS.valid_min = 0
    temperature_qcS.valid_max = 9
    temperature_qcS[:] = temperature_qc

    conductivity_qcS = dataset.createVariable("conductivity_qc", "i1", ("time",), fill_value = -127)
    conductivity_qcS.flag_meanings = "no_qc_performed good_data probably_good_data bad_data_that_are_potentially_correctable bad_data value_changed not_used not_used interpolated_value missing_value"
    conductivity_qcS.flag_values = qc_val
    conductivity_qcS.long_name = "conductivity Quality Flag"
    conductivity_qcS.standard_name = "sea_water_electrical_conductivity status_flag"
    conductivity_qcS.valid_min = 0
    conductivity_qcS.valid_max = 9
    conductivity_qcS[:] = conductivity_qc

    salinity_qcS = dataset.createVariable("salinity_qc", "i1", ("time",), fill_value = -127)
    salinity_qcS.flag_meanings = "no_qc_performed good_data probably_good_data bad_data_that_are_potentially_correctable bad_data value_changed not_used not_used interpolated_value missing_value"
    salinity_qcS.flag_values = qc_val
    salinity_qcS.long_name = "salinity Quality Flag"
    salinity_qcS.standard_name = "sea_water_salinity status_flag"
    salinity_qcS.valid_min = 0
    salinity_qcS.valid_max = 9
    salinity_qcS[:] = salinity_qc

    density_qcS = dataset.createVariable("density_qc", "i1", ("time",), fill_value = -127)
    density_qcS.flag_meanings = "no_qc_performed good_data probably_good_data bad_data_that_are_potentially_correctable bad_data value_changed not_used not_used interpolated_value missing_value"
    density_qcS.flag_values = qc_val
    density_qcS.long_name = "density Quality Flag"
    density_qcS.standard_name = "sea_water_density status_flag"
    density_qcS.valid_min = 0
    density_qcS.valid_max = 9
    density_qcS[:] = density_qc

    profile_time_qcS = dataset.createVariable("profile_time_qc", "i1", fill_value = -127)
    profile_time_qcS.flag_meanings = "no_qc_performed good_data probably_good_data bad_data_that_are_potentially_correctable bad_data value_changed not_used not_used interpolated_value missing_value"
    profile_time_qcS.flag_values = qc_val
    profile_time_qcS.long_name = "profile_time Quality Flag"
    profile_time_qcS.standard_name = "time status_flag"
    profile_time_qcS.valid_min = 0
    profile_time_qcS.valid_max = 9
    profile_time_qcS[:] = profile_time_qc

    profile_lat_qcS = dataset.createVariable("profile_lat_qc", "i1", fill_value = -127)
    profile_lat_qcS.flag_meanings = "no_qc_performed good_data probably_good_data bad_data_that_are_potentially_correctable bad_data value_changed not_used not_used interpolated_value missing_value"
    profile_lat_qcS.flag_values = qc_val
    profile_lat_qcS.long_name = "profile_lat Quality Flag"
    profile_lat_qcS.standard_name = "latitude status_flag"
    profile_lat_qcS.valid_min = 0
    profile_lat_qcS.valid_max = 9
    profile_lat_qcS[:] = profile_lat_qc

    profile_lon_qcS = dataset.createVariable("profile_lon_qc", "i1", fill_value = -127)
    profile_lon_qcS.flag_meanings = "no_qc_performed good_data probably_good_data bad_data_that_are_potentially_correctable bad_data value_changed not_used not_used interpolated_value missing_value"
    profile_lon_qcS.flag_values = qc_val
    profile_lon_qcS.long_name = "profile_lon Quality Flag"
    profile_lon_qcS.standard_name = "longitude status_flag"
    profile_lon_qcS.valid_min = 0
    profile_lon_qcS.valid_max = 9
    profile_lon_qcS[:] = profile_lon_qc

    time_uv_qcS = dataset.createVariable("time_uv_qc", "i1", fill_value = -127)
    time_uv_qcS.flag_meanings = "no_qc_performed good_data probably_good_data bad_data_that_are_potentially_correctable bad_data value_changed not_used not_used interpolated_value missing_value"
    time_uv_qcS.flag_values = qc_val
    time_uv_qcS.long_name = "time_uv Quality Flag"
    time_uv_qcS.standard_name = "time status_flag"
    time_uv_qcS.valid_min = 0
    time_uv_qcS.valid_max = 9
    time_uv_qcS[:] = time_uv_qc

    lat_uv_qcS = dataset.createVariable("lat_uv_qc", "i1", fill_value = -127)
    lat_uv_qcS.flag_meanings = "no_qc_performed good_data probably_good_data bad_data_that_are_potentially_correctable bad_data value_changed not_used not_used interpolated_value missing_value"
    lat_uv_qcS.flag_values = qc_val
    lat_uv_qcS.long_name = "lat_uv Quality Flag"
    lat_uv_qcS.standard_name = "latitude status_flag"
    lat_uv_qcS.valid_min = 0
    lat_uv_qcS.valid_max = 9
    lat_uv_qcS[:] = lat_uv_qc

    lon_uv_qcS = dataset.createVariable("lon_uv_qc", "i1", fill_value = -127)
    lon_uv_qcS.flag_meanings = "no_qc_performed good_data probably_good_data bad_data_that_are_potentially_correctable bad_data value_changed not_used not_used interpolated_value missing_value"
    lon_uv_qcS.flag_values = qc_val
    lon_uv_qcS.long_name = "lon_uv Quality Flag"
    lon_uv_qcS.standard_name = "longitude status_flag"
    lon_uv_qcS.valid_min = 0
    lon_uv_qcS.valid_max = 9
    lon_uv_qcS[:] = lon_uv_qc

    u_qcS = dataset.createVariable("u_qc", "i1", fill_value = -127)
    u_qcS.flag_meanings = "no_qc_performed good_data probably_good_data bad_data_that_are_potentially_correctable bad_data value_changed not_used not_used interpolated_value missing_value"
    u_qcS.flag_values = qc_val
    u_qcS.long_name = "u Quality Flag"
    u_qcS.standard_name = "eastward_sea_water_velocity status_flag"
    u_qcS.valid_min = 0
    u_qcS.valid_max = 9
    u_qcS[:] = u_qc

    v_qcS = dataset.createVariable("v_qc", "i1", fill_value = -127)
    v_qcS.flag_meanings = "no_qc_performed good_data probably_good_data bad_data_that_are_potentially_correctable bad_data value_changed not_used not_used interpolated_value missing_value"
    v_qcS.flag_values = qc_val
    v_qcS.long_name = "v Quality Flag"
    v_qcS.standard_name = "northward_sea_water_velocity status_flag"
    v_qcS.valid_min = 0
    v_qcS.valid_max = 9
    v_qcS[:] = v_qc

    # --- Define global attributes: ---
    dataset.Conventions = conventions_global
    dataset.Metadata_Conventions = Metadata_Conventions_global
    dataset.acknowledgment = acknowledgment_global
    dataset.comment =  comment_global
    dataset.contributor_name = contributor_name_global
    dataset.contributor_role = contributor_role_global
    dataset.creator_email = creator_email_global
    dataset.creator_name = creator_name_global
    dataset.creator_url = creator_url_global
    dataset.date_created = date_created_global
    dataset.date_issued = date_issued_global
    dataset.date_modified = date_modified_global
    dataset.format_version = format_version_global
    dataset.history = history_global
    dataset.id = id_global
    dataset.institution = institution_global
    dataset.keywords = keywords_global
    dataset.keywords_vocabulary = keywords_vocabulary_global
    dataset.license = license_global
    dataset.metadata_link = metadata_link_global
    dataset.naming_authority = naming_authority_global
    dataset.platform_type = platform_type_global
    dataset.processing_level = processing_level_global
    dataset.project = project_global
    dataset.publisher_email = publisher_email_global
    dataset.publisher_name = publisher_name_global
    dataset.publisher_url = publisher_url_global
    dataset.references = references_global
    dataset.sea_name = sea_name_global
    dataset.source = source_global
    dataset.standard_name_vocabulary = standard_name_vocabulary_global
    dataset.summary = summary_global
    dataset.title = title_global
    dataset.wmo_id = sgwmo

    # --- Finally, let's write everything into the nc file: ---
    dataset.close()

    # --- write entry in tmpdel_update_history file: ---
    cmd = "echo " + fo_name + " " + str(dive_number_in) + " " + out_type + " | awk \' { printf\"    %s    (dive: %3d %s)\\n\", $1, $2, $3 } \' >> " + dir_out_nc2IOOS + "/update_history"
    os.system(cmd)
#======================================================================





sgwmo, id_global, metadata_link_global, ctd_serial_number, ctd_calib_date, trajectory, ctd_type, sea_name_global = ("",) * 8



try:
    filein = open('/home/martink/scripts/2020/SG601_MD.ini', 'r')
except IOError:
    print('[SGnc2AOMLnc] ERROR: metadata file ./SG601_MD.ini is empty or does not exist!!!')
    exit()


for line in filein:
    recs = line.split()
    #print (recs)
    if len(recs) >= 4 and recs[0] == sgid and recs[2] == "sgwmo": sgwmo = recs[3]
    if len(recs) >= 4 and recs[0] == sgid and recs[2] == "id_global": id_global = recs[3]
    if len(recs) >= 4 and recs[0] == sgid and recs[2] == "metadata_link_global": metadata_link_global = recs[3]
    if len(recs) >= 4 and recs[0] == sgid and recs[2] == "ctd_serial_number": ctd_serial_number = recs[3]
    if len(recs) >= 4 and recs[0] == sgid and recs[2] == "ctd_calib_date": ctd_calib_date = recs[3]
    if len(recs) >= 4 and recs[0] == sgid and recs[2] == "trajectory": trajectory = recs[3]
    if len(recs) >= 4 and recs[0] == sgid and recs[2] == "ctd_type": ctd_type = recs[3]
    if len(recs) >= 4 and recs[0] == sgid and recs[2] == "sea_name_global":
        if recs[3] == "North":
            sea_name_global = "Gulf of Mexico"
        else:
            sea_name_global = "Gulf of Mexico"

#print (recs,sgwmo,id_global,metadata_link_global,ctd_serial_nif record == '[:]':
                command = "temp_name[:] = np.NaN"
                exec(command)umber,ctd_calib_date,trajectory,ctd_type,sea_name_global)




#===================== --- Reading Seaglider file_in --- =====================

# --- Open file_in for reading ---
try:
    dataset = Dataset(file_in)
except IOError:
    print('[SGnc2IOOSnc] ERROR: input file ' + file_in + ' is empty or does not exist!!!')
    exit()

# --- reading parameters, attributes and variables from file_in ---
sgname = dataset.variables['glider'].call_sign      # reading 'call_sign' attribute from variable 'glider'
date_created_global = dataset.date_created          # reading 'date_created' global attribute

dive_number_in = dataset.dive_number
profile_dn = 2 * dive_number_in - 1
profile_up = 2 * dive_number_in;

if ctd_type == "ctsail":
    dim_id = "sg_data_point"
else:
    dim_id = "ctd_data_point"

sg_dim = dataset.dimensions[dim_id].size        # reading the size of the main dimension (sg_data_point or ctd_data_point) for data variables

depth_in = dataset.variables['ctd_depth'][:]    # reading nc variable 'ctd_depth' in depth_in
ndn = numpy.argmax(depth_in) + 1
nup = len(depth_in)
depth_dn = depth_in[0 : ndn]
depth_up = depth_in[ndn : nup]

time_in = dataset.variables['ctd_time'][:]
time_dn = time_in[0 : ndn ]
time_up = time_in[ndn : nup]

lat_in = dataset.variables['latitude'][:]
lat_dn = lat_in[0 : ndn]
lat_up = lat_in[ndn : nup]

lon_in = dataset.variables['longitude'][:]
lon_dn = lon_in[0 : ndn]
lon_up = lon_in[ndn : nup]

if ctd_type == "ctsail":
    pressure_in = dataset.variables['pressure'][:]
elif ctd_type == "gpctd":
    # In this case we calculate pressure from depth using CSIRO's Seawater_ver3_3.1, as follows:
    #       DEG2RAD = pi/180;
    #       X       = sin(abs(LAT)*DEG2RAD);  % convert to radians
    #       C1      = 5.92E-3+X.^2*5.25E-3;
    #       pres    = ((1-C1)-sqrt(((1-C1).^2)-(8.84E-6*DEPTH)))/4.42E-6;
    D2R = numpy.pi/180      # convert to radians
    Xin = numpy.sin(abs(lat_in) * D2R)
    Cin = 5.92E-3 + Xin**2 * 5.25E-3
    pressure_in = ( (1 - Cin) - numpy.sqrt( ( (1 - Cin)**2 ) - ( 8.84E-6 * depth_in ) ) ) / 4.42E-6
elif ctd_type == "scicon":
    pressure_in = dataset.variables['ctd_pressure'][:]
pressure_dn = pressure_in[0 : ndn]
pressure_up = pressure_in[ndn : nup]

temperature_in = dataset.variables['temperature'][:]
temperature_dn = temperature_in[0 : ndn]
temperature_up = temperature_in[ndn : nup]

conductivity_in = dataset.variables['conductivity'][:]
conductivity_dn = conductivity_in[0 : ndn]
conductivity_up = conductivity_in[ndn : nup]

salinity_in = dataset.variables['salinity'][:]
salinity_dn = salinity_in[0 : ndn]
salinity_up = salinity_in[ndn : nup]

density_in = dataset.variables['density'][:]
density_dn = density_in[0 : ndn]
density_up = density_in[ndn : nup]

mid_dn = int( len(time_dn) / 2 )
mid_up = int( len(time_up) / 2 )

profile_time_dn = time_dn[mid_dn]
profile_time_up = time_up[mid_up]

profile_lat_dn = lat_dn[mid_dn]
profile_lat_up = lat_up[mid_up]

profile_lon_dn = lon_dn[mid_dn]
profile_lon_up = lon_up[mid_up]

time_uv_dn = profile_time_dn
time_uv_up = profile_time_up

lat_uv_dn = profile_lat_dn
lat_uv_up = profile_lat_up

lon_uv_dn = profile_lon_dn
lon_uv_up = profile_lon_up

u_in = dataset.variables['depth_avg_curr_east'][:]
u_dn = u_up = u_in

v_in = dataset.variables['depth_avg_curr_north'][:]
v_dn = v_up = v_in

# --- since we do not apply QC to this variables, let's just assign value 0:
time_qc_dn = lat_qc_dn = lon_qc_dn = pressure_qc_dn = depth_qc_dn = density_qc_dn = [0] * ndn
time_qc_up = lat_qc_up = lon_qc_up = pressure_qc_up = depth_qc_up = density_qc_up = [0] * (nup - ndn)
profile_time_qc_dn = profile_lat_qc_dn = profile_lon_qc_dn = time_uv_qc_dn = lat_uv_qc_dn = lon_uv_qc_dn = 0
profile_time_qc_up = profile_lat_qc_up = profile_lon_qc_up = time_uv_qc_up = lat_uv_qc_up = lon_uv_qc_up = 0

temperature_qc_in = map(int, dataset.variables['temperature_qc'][:])    # reading variable 'temperature_qc' and converting the values to integers
temperature_qc_dn = temperature_qc_in[0 : ndn]
temperature_qc_up = temperature_qc_in[ndn : nup]

conductivity_qc_in = map(int, dataset.variables['conductivity_qc'][:])
conductivity_qc_dn = conductivity_qc_in[0 : ndn]
conductivity_qc_up = conductivity_qc_in[ndn : nup]

salinity_qc_in = map(int, dataset.variables['salinity_qc'][:])
salinity_qc_dn = salinity_qc_in[0 : ndn]
salinity_qc_up = salinity_qc_in[ndn : nup]

uv_qc_in = map(int, dataset.variables['depth_avg_curr_qc'][:])
u_qc_dn = v_qc_dn = u_qc_up = v_qc_up = uv_qc_in
#======================================================================



# ---- writing values to file_out_dn
write_file_out("dn")

# ---- writing values to file_out_up
write_file_out("up")

# ---- exit
exit()
