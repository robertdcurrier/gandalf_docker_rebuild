#!/bin/bash

curl --http1.1 -X POST https://developer-mission.saildrone.com/v1/ais --header 'Content-Type: application/json'  --header 'authorization: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbiI6ImUwZTkxNWM4LTZkZWUtNGEyZC1iMTVhLThiY2E2OWVkODQ0YSIsImtleSI6ImU0cWVSdVpxdVRSVmduclIiLCJpYXQiOjE2NjAxMzk0MDYsImV4cCI6MTY2NzkxNTQwNn0.kfyMnlW8Jnb8MV0ijcxEGsLbdMHcW1asyTJLPeaMmLc' -d '{
"mmsi": "ng427", 
"longitude": -74.7303,
"latitude": 31.1986, 
"timestamp": 1660060800,
"token" : "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbiI6ImUwZTkxNWM4LTZkZWUtNGEyZC1iMTVhLThiY2E2OWVkODQ0YSIsImtleSI6ImU0cWVSdVpxdVRSVmduclIiLCJpYXQiOjE2NjAxMzk0MDYsImV4cCI6MTY2NzkxNTQwNn0.kfyMnlW8Jnb8MV0ijcxEGsLbdMHcW1asyTJLPeaMmLc"
}'

