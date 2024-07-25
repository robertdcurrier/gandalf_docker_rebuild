#!/bin/bash 
echo "Using jsmin on web to minify JS..."
docker exec web sh -c "cd /var/www/wsgi/gandalf/app/static/js &&
 python3 -m jsmin *.js > dist/build.min.js"
