#!/bin/bash
echo "Making top level directories..."
mkdir ascii_files
mkdir binary_files
mkdir processed_data
mkdir plots
mkdir kmz
mkdir json
echo "Making binary directories..."
cd binary_files
mkdir sbd
mkdir tbd
mkdir ebd
mkdir dbd
cd ..
echo "Making  ascii directories..."
cd ascii_files
mkdir logs
mkdir mlg
mkdir nlg
cd ..
echo "Making processed_data directories..."
cd processed_data
mkdir dba 
mkdir ngdac_files
cd dba
mkdir flight
mkdir science
mkdir merged
cd ..
cd ..
echo "Done!"


