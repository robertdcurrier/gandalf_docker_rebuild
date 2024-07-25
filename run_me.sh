#!/bin/bash

# Check if /Volumes directory exists
if [ -d "/Volumes" ]; then
    # Check if /Volumes/data directory exists
    if [ -d "/Volumes/data" ]; then
        echo "Found /Volumes/data. Creating symlink 'data' pointing to /Volumes/data."
        ln -sfn /Volumes/data data
    fi
else
    echo "/Volumes directory not found. Creating symlink 'data' pointing to /data."
    ln -sfn /data data
fi

# List of images to check
images=("gandalf_web" "gandalf_tools")

# Function to check if a Docker image exists locally
check_image() {
  local image=$1
  if ! docker image inspect "$image" > /dev/null 2>&1; then
    return 1
  fi
}

# Iterate over the list of images and check each one
for image in "${images[@]}"; do
  if ! check_image "$image"; then
    echo "Image $image not found locally. Exiting."
    exit 1
  fi
done

echo "All images are present locally."

# Up time
echo "Moving on up..."
docker compose up -d

# Dropped GULP now using jsmin
echo "Using jsmin on web to minify JS..."
docker exec gandalf_web sh -c "cd /var/www/wsgi/gandalf/app/static/js &&
 python3 -m jsmin *.js > dist/build.min.js"

