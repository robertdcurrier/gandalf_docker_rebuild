#!/usr/bin/env python3
"""
Created:    2023-09-14
Modified:   2023-09-14
Author:     bob.currier@gcoos.org
Notes:      Pulls png files of model comparison for deployed
			 vehicles from Rutgers
"""
import logging
import sys
import time
from bs4 import BeautifulSoup
from datetime import datetime
from datetime import date
from datetime import timedelta
from urllib.request import urlopen
logging.basicConfig(level=logging.WARNING)
# GLOBALS --> Need to move to ngdac.json Gandalf section
model_root_url = "https://rucool.marine.rutgers.edu/hurricane/\
model_comparisons/profiles/gliders"
output_dir = "/data/gandalf/deployments/model_comps"
# END GLOBALS


def get_file_names(comps_url):
	"""
	Created:    2023-09-14
	Modified:   2023-09-14
	Author:     bob.currier@gcoos.org
	Notes:      Pulls png files of model comparison for deployed
				 vehicles from Rutgers
	"""
	logging.info(f'get_file_names(): Using {comps_url}')
	logging.info(f'get_file_names()" Writing to {output_dir}')
	with urlopen(comps_url) as file:
	    try:
	        raw_html = file.read()
	    except:
	        logging.warning(f'get_file_names(): Failed to load url')
	fnames = bs4_parse(raw_html)
	logging.debug(f'get_file_names(): Got {fnames}')
	return (fnames)


def bs4_parse(raw_html):
	"""
	Created:    2023-09-14
	Modified:   2023-09-14
	Author:     bob.currier@gcoos.org
	Notes:      Uses BeautifulSoup to parse html doc from url
	"""
	png_files = []
	logging.debug(f'bs4_parse()')
	soup = BeautifulSoup(raw_html, 'html.parser')
	# Select all a tags
	images = soup.select('a')
	# look only for png hrefs
	for fname in images:
		if 'png' in str(fname):
			png_files.append(fname.text)
	return png_files


def modcomp_fetch_png_files(fnames, comps_url):
	"""
	Created:    2023-09-14
	Modified:   2023-09-15
	Author:     bob.currier@gcoos.org
	Notes:      Retrieves deployed glider model png files from Rutgers
				2023-09-15 fixed bug in file_path
	"""
	for png_file in fnames:
		file_path = f'{comps_url}/{png_file}'
		with urlopen(file_path) as file:
			logging.warning(f'modcomp_fetch_png_files(): Downloading {png_file}')
			try:
				content = file.read()
			except:
				logging.warning(f'fetch_rtofs(): Failed to download {png_file}')
				sys.exit()
		try:
			out_file = open(f'/data/gandalf/deployments/model_comps/{png_file}', "wb")
			out_file.write(content)
		except:
			logging.warning('modcomp_fetch_png_files(): Failed to write content to file.')
			sys.exit()


def gandalf_model_comps():
	"""
	Created:    2023-09-14
	Modified:   2023-09-14
	Author:     bob.currier@gcoos.org
	Notes:		Main entry point
	"""
	logging.info(f'gandalf_model_comps()')
	today = (date.today())
	# Yesterday to make sure all vehicles have updated
	yesterday = str(today - timedelta(days=1))
	(year,month,day) = yesterday.split('-')
	comps_url = f"{model_root_url}/{year}/{month}-{day}"

	fnames = get_file_names(comps_url)
	modcomp_fetch_png_files(fnames, comps_url)


if __name__ == '__main__':
	logging.basicConfig(level=logging.WARNING)
	start_time = time.time()
	gandalf_model_comps()
	end_time = time.time()
	minutes = round((end_time - start_time) / 60, 2)
	logging.warning(f'Duration: {minutes} minutes')
