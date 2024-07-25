
function showLastPos(feature, map) {
  console.log("showLastPos()");
  console.log("Using public_name: " + feature.properties.public_name);
  var currPosIcon = L.icon({
    iconUrl: feature.properties.currPosIcon,
    iconSize: feature.properties.iconSize
  });
  var wpIcon = L.icon({
    iconUrl: feature.properties.wpIcon,
    iconSize: feature.properties.iconSize
  });
  lon = feature.geometry.coordinates[0];
  lat = feature.geometry.coordinates[1];
  bearing = 0;
  lastPos = L.marker([lat, lon], {icon: currPosIcon, rotationAngle: bearing});
  lastPos.bindPopup(feature.properties.html)
  lastPos.bindTooltip(feature.properties.public_name.toUpperCase());
  lastPos.addTo(map)
}

function makeLayer(the_markers) {
  console.log('makeLayer()...');
  theLayer = L.layerGroup();
  for (const marker of the_markers) {
    marker.addTo(theLayer);
  }
  return theLayer;
}

// We can use same function for all layer markers
function makeSurfMarker(feature) {
  lon = feature.geometry.coordinates[0];
  lat = feature.geometry.coordinates[1];
  var circle = L.circleMarker([lat, lon], {
    radius: feature.properties.radius,
    color:  feature.properties.marker_color,
    fillColor: feature.properties.fillColor,
    fillOpacity: feature.properties.opacity,
    weight: feature.properties.weight,
    opacity: feature.properties.fillOpacity
  });
  circle.bindPopup(feature.properties.html);
  return(circle)
}

function clearCworkerLayers() {
  console.log('clearCworkerLayers()...')
  tempLayer.remove();
  salinityLayer.remove();
  oxyLayer.remove();
}

function showCworker(map) {
  var data_file = '/data/gandalf/deployments/geojson/cworker.json'
  // Storage for our sensor markers  -- these get turned into L.LayerGroups
  var temperature_markers = []
  var salinity_markers = []
  var oxy_markers = []
  console.log('showCworker(): fetching cworker.json');
  var fC = $.getJSON(data_file, function() {
  })
  .done(function() {
        L.geoJson(fC.responseJSON, {
        onEachFeature: function(feature, layer) {
          // add track with styling
          if (feature.id == 'track') {
            console.log('showCworker(): Adding track...')
            cwTrack = L.geoJson(feature, {style: feature.properties.style});
            cwTrackLayer  = L.layerGroup([cwTrack]);
            cwTrackLayer.addTo(map);
          }
          //Temp layer
          if (feature.id == 'sea_water_temperature_marker') {
            sm = makeSurfMarker(feature)
            temperature_markers.push(sm)
          }
           //Salinity layer
          if (feature.id == 'sea_water_practical_salinity_marker') {
            sm = makeSurfMarker(feature);
            salinity_markers.push(sm)
          }
           //Oxy layer
          if (feature.id == 'volume_fraction_of_oxygen_in_sea_water_marker') {
            sm = makeSurfMarker(feature);
            oxy_markers.push(sm);
          }
      
          // add last position with styling
          if (feature.id == 'last_pos') {
            showLastPos(feature, map);
          }
        }
    })
    tempLayer = makeLayer(temperature_markers);
    salinityLayer = makeLayer(salinity_markers);
    oxyLayer = makeLayer(oxy_markers);

    // Default layer is temperature
    tempLayer.addTo(map);
  })

  // CW ASV layers
  // No layers on map
  $("#cw_none").click(function() {
    console.log('Removing all CW Layers')
    isChecked = ($('#cw_none').prop('checked'));
    if (isChecked) {
      clearCworkerLayers();
   }
  });
  // track
  $("#cworker_track").click(function() {
    isChecked = ($('#cworker_track').prop('checked'));
    if (isChecked) {
     console.log('Adding cworker_track layer...')
     cwTrackLayer.addTo(map)
   } else {
     console.log('Removing CW track layer...')
     cwTrackLayer.remove();
   }
  });
   // temp
  $("#cw_temp").click(function() {
    isChecked = ($('#cw_temp').prop('checked'));
    if (isChecked) {
     console.log('Adding CW temp layer...')
     tempLayer.addTo(map)
    }
  });
  // salinity
  $("#cw_psal").click(function() {
    isChecked = ($('#cw_psal').prop('checked'));
    if (isChecked) {
     clearCworkerLayers();
     console.log('Adding CW Salinity layer...')
     salinityLayer.addTo(map)
    }
  });
  // oxy
  $("#cw_oxy").click(function() {
    isChecked = ($('#cw_oxy').prop('checked'));
    if (isChecked) {
     clearCworkerLayers();
     console.log('Adding CW Oxy layer...')
     oxyLayer.addTo(map)
    }
  });
   // track
  $("#cworker_track").click(function() {
    isChecked = ($('#cworker_track').prop('checked'));
    if (isChecked) {
     console.log('Adding cworker_track layer...')
     cwTrackLayer.addTo(map)
   } else {
     console.log('Removing CW track layer...')
     cwTrackLayer.remove();
   }
  });
}  
