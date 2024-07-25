2017-10-30
Now running on gcoos4 since gcoos2 gorked.
Important things to note: This is an old and crufty system and is not
well installed, maintained or operated. A full desktop install of CentOS7
was done leaving hordes of useless Xlib stuff and apps lying about. There has
never been a good yum update and trying to do a full system update breaks badly. I
tried several workarounds and finally gave up.

There are conflicting versions of httpd installed. The default /usr/sbin/httpd is 
actually /opt/httpd-2.4.23 instead of the correct /usr/sbin/httpd-2.4.6. Mod_WSGI
would NOT work with the running 2.4.23.  I stopped that version, made the changes 
to the httpd.conf file for 2.4.6 and restarted. Finally got mod_wsgi going. It appears
that SB's thredds/errdap stuff still works. 

PostGIS was a bitch. There were no PostGIS extensions installed so had to do that. Then
a big struggle with finding the right pg_hba.conf and the proper settings for the 
postgres user. Different than on gcoos2 and itag. Finally got that working with psycopg2.

I copied wg_track.json over from itag.gcoos.org as I could not generate here due to 
lack of speed and heading variables as the WG is on the bench and not in the water. 

Data will need to changed to all point here instead of gcoos2.

Removed the DB_USER and DB_PASSWORD env settings from gandalf_utils as they are just
a pain in the ass on this system. 

Figured out how not to have use symlink for /data. Changed httpd and added
Alias '/data' '/data' directive. Had to define /data as a <Directory> and add
Options FollowSymLinks to make this work. No need now for the gandalf_data symlink.


