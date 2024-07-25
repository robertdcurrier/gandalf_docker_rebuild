#!/usr/bin/env python3
"""
Created: 2020-05-26
Notes: Maps chloro maps for GANDALF map display
"""
import json
import sys
import pandas as pd
import numpy as np
from datetime import datetime
from geojson import Feature, Point, FeatureCollection, LineString
from gandalf_utils import get_vehicle_config, flight_status, dinkum_convert
from chloroMap import chloroMap

def cmap_chloro(value, min, max):
    """
    """
    index = int((254/max) * value)
    hexString = chloroMap[index];
    return hexString


def chloro_map(config, vehicle):
    """
    New 'heat map' display for sensors to facilitate easy visualization
    of GPS coordinates with sensor readings.
    Modified: 2020-05-26
    """
    # hardwired until I get working for all vehicles
    data_dir = config['gandalf']['deployed_data_dir']
    print('chloro_map(%s)' % data_dir)
    chloro_markers = []
    #read CSV
    file_name = "%s/processed_data/sensors.csv" % (data_dir)
    data_frame = pd.read_csv(file_name)
    print('chloro_map(): Interpolating...')
    data_frame['sci_flbbcd_chlor_units'] = (data_frame['sci_flbbcd_chlor_units']
                                            .interpolate(method='nearest'))
    data_frame['m_lon'] = (data_frame['m_lon']
                            .interpolate(method='nearest'))
    data_frame['m_lat'] = (data_frame['m_lat']
                            .interpolate(method='nearest'))
    data_frame['m_depth'] = (data_frame['m_depth']
                            .interpolate(method='nearest'))
    m_depth_max = int(data_frame['m_depth'].max())
    data_frame_len = (len(data_frame))
    print(data_frame['sci_flbbcd_chlor_units'].max())
    if data_frame_len == 0:
        print('heat_map_json(): Empty Data Frame')
        return
    print("chloro_map(): Dropping dupes")
    data_frame = data_frame.drop_duplicates(subset=('m_lon','m_lat'))
    data_frame = data_frame.reset_index(drop=True)
    # Dinkum converting GPS coordinates
    print('chloro_map(): Dinkum converting...')
    for idx, row in data_frame.iterrows():
        if np.isfinite(row['m_lon']):
            (lon, lat) = dinkum_convert(row['m_lon'],row['m_lat'])
            data_frame.iloc[idx]['m_lat'] = lat
            data_frame.iloc[idx]['m_lon'] = lon
        else:
            data_frame.iloc[idx]['m_lat'] = 0.0
            data_frame.iloc[idx]['m_lon'] = 0.0

    hm_df = data_frame[['m_lon', 'm_lat', 'm_depth',
                        'm_present_time', 'sci_flbbcd_chlor_units']].copy()
    hm_df = hm_df.dropna()

    for idx, row in hm_df.iterrows():
        point = Point([float(row['m_lon']), float(row['m_lat'])])
        surf_marker = Feature(geometry=point, id='surf_marker')
        chloro_color = cmap_chloro(row['sci_flbbcd_chlor_units'],0, 8)
        chloro_time = (datetime.fromtimestamp(row['m_present_time']).
                                             strftime("%Y-%m-%d %H:%M UTC"))
        m_depth =row['m_depth']
        chloro_radius = 5
        np.nanmax(data_frame['m_present_time'])
        # Properties -- need to move this to config file
        surf_marker.properties['sci_flbbcd_chlor_units'] = row['sci_flbbcd_chlor_units']
        surf_marker.properties['chloro_depth'] = row['m_depth']
        surf_marker.properties['chloro_color'] = chloro_color
        surf_marker.properties['chloro_fill_color'] = chloro_color
        surf_marker.properties['chloro_radius'] = chloro_radius
        surf_marker.properties['chloro_weight'] = .8
        surf_marker.properties['chloro_opacity'] = 1
        surf_marker.properties['chloro_fill_opacity'] = 1
        infobox_image = config["gandalf"]["infoBoxImage"]

        surf_marker.properties['html'] = """
            <center><img src='%s'></img></center>
            <hr>
            <h5><center><span class='infoBoxHeading'>chL-a</span></center></h5>
            <table class='infoBoxTable'>
            <tr><td class='td_infoBoxSensor'>Date/Time:</td><td>%s</td></tr>
            <tr><td class='td_infoBoxSensor'>Position:</td><td>%sW/%sN</td></tr>
            <tr><td class='td_infoBoxSensor'>Depth(m):</td><td>%s</td></tr>
            <tr><td class='td_infoBoxSensor'>Chlorophyll:</td><td>%s</td></tr>
            </table>
            """ % (infobox_image, chloro_time, row['m_lon'], row['m_lat'],
                    row['m_depth'], row['sci_flbbcd_chlor_units'])

        chloro_markers.append(surf_marker)
    fC = FeatureCollection(chloro_markers)
    return(fC)


def write_geojson_file(data_source, data):
    """
    Modified: 2020-05-26
    Notes: D'oh. Writes out geojson file for Jquery AJAX loading
    """
    print("write_geojson_file(%s)" % data_source)
    fname = '/data/gandalf/deployments/geojson/%s.json' % data_source
    outf = open(fname, 'w')
    print(data, file=outf)
    outf.flush()
    outf.close()


if __name__ == '__main__':
    if len(sys.argv) > 1:
            vehicle = sys.argv[1]
    else:
        print("Usage: gandalf_chloro_map vehicle_name")
        sys.exit()
        
    config = get_vehicle_config(vehicle)
    fC = chloro_map(config, vehicle)
    write_geojson_file('chloro', fC)
