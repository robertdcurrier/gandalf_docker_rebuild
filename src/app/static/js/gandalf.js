function initPortalMap(vehicle_type, json_file) {
  /*
   * We initialize a map strictly for the data portal.
   * No layers or Windy stuff. We do this as a separate
   * map so we don't interfere with the other maps. Might
   * be a way to drop everthing on gandalfMap, but we don't
   * want Windy... so will keep it separate for now.
   *
  */
  console.log("initPortalMap()");
   var portalMap = L.map('portalMap', {
    zoomControl: false
  });

  portalMap.setView([31, -88.7], 6);
  // Put zoom where we want...
  L.control.zoom({
    position: 'bottomright'
  }).addTo(portalMap);
  // Basemap
  var esri_url = "https://server.arcgisonline.com/ArcGIS/rest/services/"+
  "Ocean_Basemap/MapServer/tile/{z}/{y}/{x}";
  var esri_attribution = "Tiles &copy; Esri &mdash; Sources: GEBCO, NOAA"
  var openOcean = L.tileLayer(noaa_charts, {attribution: esri_attribution,
    maxZoom: 17,
    maxNativeZoom: 13,
    opacity: 1}).addTo(portalMap);
    portalMap.scrollWheelZoom.disable();

  L.control.coordinates({
    position: "bottomleft",
    decimals: 4,
    decimalSeperator: "."
  }).addTo(portalMap);

  // Each vehicle type has its own method for getting dropped on map
  if(vehicle_type == 'slocum') {
    showLocalVehicles(portalMap, json_file);
  }
  if(vehicle_type == 'navocean') {
    showNavoceanColorMap(portalMap, json_file);
  }
}

function parseBoolValue(value) {
var new_value;
if (value === undefined) new_value = false;
if (value === 'true' || value == true) new_value = true;
else if (value === 'false' || value == false) new_value = false;
else new_value = false;
return new_value;
};


function initGANDALF(map_center, map_zoom) {
  var fleet_id = "5c1d509d5199afbbabc42c87c8a8ecc3";
  console.log('initGANDALF()');
  gandalfMap = L.map('map', {
    zoomControl: false,
  });
  gandalfMap.setView(map_center, map_zoom);
  // Put zoom where we want...
  L.control.zoom({
    position: 'bottomright'
  }).addTo(gandalfMap);
  // Basemap
  var esri_url = ("https://server.arcgisonline.com/ArcGIS/rest/services/" +
  "NatGeo_World_Map/MapServer/tile/{z}/{y}/{x}");
  var esri_attribution = "Tiles &copy; Esri &mdash; Sources: GEBCO, NOAA"
  var esri_tiles = L.tileLayer(esri_url, {
                                              attribution: esri_attribution,
                                              maxZoom: 17, maxNativeZoom: 10,
                                              opacity: 1
                                            }
                              );

    esri_tiles.addTo(gandalfMap);

    gandalfMap.scrollWheelZoom.enable();
    gandalfMap.doubleClickZoom.enable();

  L.control.coordinates({
    position: "bottomleft",
    decimals: 4,
    decimalSeperator: "."
  }).addTo(gandalfMap);

  // DOM STUFF
  $("#lsuSST").click(function() {
    sstLegend();
  });

  $("#lsuUnmasked").click(function() {
    sstLegend();
  });

  $("#gcoos_gliders" ).click(function() {
    // Hide Layers if dash is opened
    $("#new-dash").hide();
    $("#gcoos_gliders").toggle();
  });
  $('#sum_deployments').text('32');
  
  $("#layerControl").click(function() {
    // Hide dash if Layers are opened
     $("#new-dash").hide();
     $("#gLayers").toggle();
   });

   $("#dash-button" ).click(function() {
     // Hide Layers if dash is opened
     $("#new-dash").toggle();
     $("#gLayers").hide();
   });

   $("#ais-all").click(function() {
      $('#map').hide();
      $('#plotWrapper').hide();
      $("#ais_map").show();
      $('#new-dash').hide();
      console.log('ALL');
   });
   $("#ais-fleet").click(function() {
       $('#map').hide();
       $('#plotWrapper').hide();
       $("#ais_map").show();
       $('#new-dash').hide();
       console.log('FLEET');
   });

   $("#closePlot" ).click(function() {
      // Hide away hide away jiggity jig but not 'X' close button
      $("#plotWrapper *:not('#closePlot')").remove();
      $("#plotWrapper").hide();
      $("#map").show();
      gandalfMap.invalidateSize();
    });

    $("#closePlot3D" ).click(function() {
      // Hide away hide away 3D jiggity jig but not 'X' close button
      $(".plot3D").remove();
      $("#plotWrapper3D").hide();
      $("#map").show();
      gandalfMap.invalidateSize();
     });
  

  // local gliders
  var data_file = '/data/gandalf/deployments/geojson/local.json'
  showLocalVehicles(gandalfMap, data_file);

  // seagliders
  var data_file = '/data/gandalf/deployments/geojson/seagliders.json'
  showSeaGliders(gandalfMap, data_file);

  // gdac gliders
  var data_file = '/data/gandalf/deployments/geojson/erddap.json'
  showErddapVehicles(gandalfMap, data_file);
  
  // erddap gliders
  var data_file = '/data/gandalf/deployments/geojson/gdac.json'
  showErddapVehicles(gandalfMap, data_file);

  // LR WaveGlider
  var random = Math.random()
  var data_file = '/data/gandalf/deployments/geojson/wg.json?random=' + random
  console.log('Using ' + data_file)
  showWaveGliders(gandalfMap, data_file);
  // ARGO floats
  var data_file = '/data/gandalf/deployments/geojson/argo.json'
  showArgoFloats(gandalfMap, data_file)
  // Seatrec floats
  var data_file = '/data/gandalf/deployments/geojson/seatrec.json'
  showSeatrecFloats(gandalfMap, data_file)

  // UGOS floats
  var data_file = '/data/gandalf/deployments/geojson/ugos.json'
  showUgosFloats(gandalfMap, data_file)

  // Now we're rocking the C-Worker
  // 2023-08-24 disabled vehicle having issues
  //showCworker(gandalfMap);

  // 2023-12-24 disabled due to hallucinations of CY's script
  addHycom(gandalfMap);

  $("#new-dash").delay(10000).fadeOut(2500, function() {
    mobile = isMobile();
    if(mobile == false) {
      s();
      console.log('LAYERS ENABLED')
    }
  });
}

function isMobile() {
  try{ document.createEvent("TouchEvent"); return true; }
  catch(e){ return false; }
}

// 2021-08-19 New shit for WaveGlider -- we borrowed heavily from Vela
function makeWgSurfMarker(feature) {
  lon = feature.geometry.coordinates[0];
  lat = feature.geometry.coordinates[1];
  radius = feature.properties.radius;
  // Need to set this in config and pass to properties
  radius_divisor = 9;
  radius = parseInt(Math.abs(feature.properties.days_wet/radius_divisor));
  zindex = radius*25000;
  var circle = L.circleMarker([lat, lon], {
    // 2021-09-02 Need to make radius scalar to age
    radius: radius,
    color:  feature.properties.marker_color,
    fillColor: feature.properties.fillColor,
    fillOpacity: feature.properties.opacity,
    weight: feature.properties.weight,
    opacity: feature.properties.fillOpacity,
    zIndexOffset: zindex
  });
  circle.bindPopup(feature.properties.html);
  return(circle)
}

function showWaveGliders(map, data_file) {
  console.log('showWaveGliders()');
  // get surf_marker_layers from config file 2021-09-08 WE ROCKED IT!
  config_file = '/data/gandalf/gandalf_configs/vehicles/sv3-076/sv3-076.cfg';
  var config = $.getJSON(config_file, function() {
  })
  .done(function() {
    var layers = config.responseJSON.surf_marker_layers;
    layers.forEach(layer => window[layer] = L.layerGroup());
    // Default is WG_Water_Temp_Layer
    WG_Water_Temp_Layer.addTo(gandalfMap);
  })

  var fC = $.getJSON(data_file, function() {
  })
  .done(function() {
    L.geoJson(fC.responseJSON, {
      //TO DO: AUTOMATE THis LIKE LAYER CREATION
      onEachFeature: function(feature, layer) {
        // Water Temperature
        if (feature.properties.index == 0) {
          showLastPos(feature, gandalfMap);
        }
        if (feature.id == 'water_temperature') {
          marker = makeWgSurfMarker(feature)
          WG_Water_Temp_Layer.addLayer(marker);
        }
        // Salinity
        if (feature.id == 'salinity') {
          marker = makeWgSurfMarker(feature)
          WG_Sal_Layer.addLayer(marker);
        }
        // Air Temp
        if (feature.id == 'air_temperature') {
          marker = makeWgSurfMarker(feature)
          WG_Air_Temp_Layer.addLayer(marker);
        }
        // Wind Speed
        if (feature.id == 'wind_speed') {
          marker = makeWgSurfMarker(feature)
          WG_Wind_Speed_Layer.addLayer(marker);
        }
        // Wave Height
        if (feature.id == 'wave_height') {
          marker = makeWgSurfMarker(feature)
          WG_Wave_Height_Layer.addLayer(marker);
        }
      }
    })
  })
}


function wgLayer(layer, image) {
    //Clears all surface markers and then adds layer of choice
    config_file = '/data/gandalf/gandalf_configs/vehicles/sv3-076/sv3-076.cfg';
    var config = $.getJSON(config_file, function() {
    })
    .done(function() {
      var layers = config.responseJSON.surf_marker_layers;
      layers.forEach(function(layer_name) {
        //console.log('Clearing ' + layer_name);
        window[layer_name].remove();
        })
        var img_root = '/data/gandalf/deployments/legends/';
        var img = '<img src="' + img_root + image + '"></img>';
        layer.addTo(gandalfMap);
        $('#wgLegend').html(img);
        $('#wgLegend').show();
      })
}
// End of WaveGlider stuff

function s() {
  console.log('s()');
  // weather.noaa.gov tropical layer
  layersNS.weatherNOAALayer.addTo(gandalfMap);
  layersNS.weatherNOAALayer.setOpacity(100);

  //BATHYMETRY
  layersNS.gebcoGridLayer.addTo(gandalfMap);
  layersNS.gebcoGridLayer.setOpacity(0);
  layersNS.noaaBagServerLayer.addTo(gandalfMap);
  layersNS.noaaBagServerLayer.setOpacity(0);
  //CHARTS
  layersNS.noaaBuoysLayer.addTo(gandalfMap);
  layersNS.noaaBuoysLayer.setOpacity(0);
  layersNS.noaaDepthsLayer.addTo(gandalfMap);
  layersNS.noaaDepthsLayer.setOpacity(0);
  //NEXRAD
  layersNS.nwsNexrad.addTo(gandalfMap);
  layersNS.nwsNexrad.setOpacity(0);
  //MODIS
  gibsMODIS1.addTo(gandalfMap);
  gibsMODIS1.setOpacity(0);
  gibsMODIS2.addTo(gandalfMap);
  gibsMODIS2.setOpacity(0);
  gibsMODIS3.addTo(gandalfMap);
  gibsMODIS3.setOpacity(0);
  //GIBS
  gibsSSTLayer.addTo(gandalfMap);
  gibsSSTLayer.setOpacity(0);
  //AOML Geostrophic
  layersNS.geostrophicLayer.addTo(gandalfMap);
  layersNS.geostrophicLayer.setOpacity(0);
  //RTOFS
  layersNS.rtofsSalinityLayer.addTo(gandalfMap);
  layersNS.rtofsSalinityLayer.setOpacity(0);
  layersNS.rtofsVelocityLayer.addTo(gandalfMap);
  layersNS.rtofsVelocityLayer.setOpacity(0);
  layersNS.rtofsSSHLayer.addTo(gandalfMap);
  layersNS.rtofsSSHLayer.setOpacity(0);
  //LSU
  layersNS.lsuSSTLayer.addTo(gandalfMap);
  layersNS.lsuSSTLayer.setOpacity(0);
  layersNS.lsuUnmaskedLayer.addTo(gandalfMap);
  layersNS.lsuUnmaskedLayer.setOpacity(0);
  //HRF
  layersNS.hfrLayer6K.addTo(gandalfMap);
  layersNS.hfrLayer6K.setOpacity(0)
  //Platforms and Pipelines and shippingLanes
  layersNS.oceanPlatformsLayer.addTo(gandalfMap);
  layersNS.oceanPlatformsLayer.setOpacity(0);
  //eez
  layersNS.eezLayer.addTo(gandalfMap);
  layersNS.eezLayer.setOpacity(0);
  // Rutgers DAC
  console.log('RUTGERS DAC')
  layersNS.rutgersDACLayer.addTo(gandalfMap);
  layersNS.rutgersDACLayer.setOpacity(0);
  // USF CHL and SST
  layersNS.sstLayer.addTo(gandalfMap);
  layersNS.sstLayer.setOpacity(0);
  layersNS.chlLayer.addTo(gandalfMap);
  layersNS.chlLayer.setOpacity(0);
}

function sstLegend() {
  var new_img = '<img src='+lsu_sst_legend+'>';
  $('#wmsLegend').html(new_img);
  $('#wmsLegend').show();
}

function showLocalVehicles(map, data_file) {
  console.log('showLocalVehicles()');
  var localGliders = []
  var fC = $.getJSON(data_file, function() {
  })
  .done(function() {
    L.geoJson(fC.responseJSON, {
        onEachFeature: function(feature, layer) {
          // add track with styling
          if (feature.id == 'track') {
            L.geoJson(feature, {style: feature.properties.style}).addTo(map);
          }
          // add last position with styling
          if (feature.id == 'last_pos') {
            showLastPos(feature, map);
          }
          if (feature.id == 'surf_marker') {
            color = 'yellow';
            lon = feature.geometry.coordinates[0];
            lat = feature.geometry.coordinates[1];
            var circle = L.circleMarker([lat, lon], {
              radius: 3,
              color:  color,
              fillColor: color,
              fillOpacity: 1,
              weight: .5,
              opacity: 1,
            });
            circle.bindPopup(feature.properties.html);
            localGliders.push(circle);
          }
        }
    })
    layersNS.localGliderLayer = L.layerGroup(localGliders);
    layersNS.localGliderLayer.addTo(map);
  })
}


function showErddapVehicles(map, data_file) {
  console.log('showErddapVehicles()');
  var fC = $.getJSON(data_file, function() {
  })
  .done(function() {
        L.geoJson(fC.responseJSON, {
        onEachFeature: function(feature, layer) {
          if (feature.id == 'track') {
            // add track with styling
            L.geoJson(feature, {style: feature.properties.style}).addTo(map);
          }
	    // add last position with styling
          if (feature.id == 'last_pos') {
            showLastPos(feature, map);
          }
        }
      })
  })
}


function showSeaGliders(map, data_file) {
  console.log('showSeaGliders()');
  var fC = $.getJSON(data_file, function() {
  })
  .done(function() {
        L.geoJson(fC.responseJSON, {
        onEachFeature: function(feature, layer) {
          if (feature.id == 'track') {
            // add track with styling
            L.geoJson(feature, {style: feature.properties.style}).addTo(map);
          }
	    // add last position with styling
          if (feature.id == 'last_pos') {
            showLastPos(feature, map);
          }
        }
      })
  })
}


function showArgoFloats(map, data_file) {
  console.log('showArgoFloats()');
  var argoMarkers = []
  var argoTrack = []
  var fC = $.getJSON(data_file, function() {
    })
    .done(function() {
      console.log('Loaded ARGO json file...');
      L.geoJson(fC.responseJSON, {
        onEachFeature: function(feature,layer){
          if(feature.id == 'surf_marker') {
            lon = feature.geometry.coordinates[0];
            lat = feature.geometry.coordinates[1];
             var marker = L.circleMarker([lat, lon], {
               radius: 5,
               color:  'black',
               fillColor: 'blue',
               fillOpacity: 1,
               weight: .8,
               opacity: 1
             });
             platformID = feature.properties.platform.toString();
             marker.bindPopup(feature.properties.html);
             marker.bindTooltip('ARGO Float ' + platformID);
             argoMarkers.push(marker);
          }
          if(feature.id == 'track') {
            console.log('adding_track');
            var trackStyle = {
              "color": "#FF00FF",
              "opacity": 1,
              "weight": 2
            }
            argoTrack.push(L.geoJson(feature, {style: trackStyle}));
          }
        }
      })
      argoMarkerLayer = L.layerGroup(argoMarkers);
      argoMarkerLayer.addTo(map);
    })
  }


function showSeatrecFloats(map, data_file) {
  console.log('showSeatrecFloats()');
  var argoMarkers = []
  var argoTrack = []
  var fC = $.getJSON(data_file, function() {
    })
    .done(function() {
      console.log('Loaded Seatrec json file...');
      L.geoJson(fC.responseJSON, {
        onEachFeature: function(feature,layer){
          if(feature.id == 'surf_marker') {
            lon = feature.geometry.coordinates[0];
            lat = feature.geometry.coordinates[1];
             var marker = L.circleMarker([lat, lon], {
               radius: 5,
               color:  'black',
               fillColor: 'yellow',
               fillOpacity: 1,
               weight: .8,
               opacity: 1
             });
             platformID = feature.properties.platform.toString();
             marker.bindPopup(feature.properties.html);
             marker.bindTooltip('Seatrec Float ' + platformID);
             argoMarkers.push(marker);
          }
          if(feature.id == 'track') {
            console.log('adding_track');
            var trackStyle = {
              "color": "#FF00FF",
              "opacity": 1,
              "weight": 2
            }
            argoTrack.push(L.geoJson(feature, {style: trackStyle}));
          }
        }
      })
      argoMarkerLayer = L.layerGroup(argoMarkers);
      argoMarkerLayer.addTo(map);
    })
  }

function showUgosFloats(map, data_file) {
  console.log('showUgosFloats()');
  var ugosMarkers = []
  var fC = $.getJSON(data_file, function() {
    })
    .done(function() {
      console.log('Loaded UGOS json file...');
      L.geoJson(fC.responseJSON, {
        onEachFeature: function(feature,layer){
          if(feature.id == 'surf_marker') {
            lon = feature.geometry.coordinates[0];
            lat = feature.geometry.coordinates[1];
             var marker = L.circleMarker([lat, lon], {
               radius: 5,
               color:  'black',
               fillColor: 'purple',
               fillOpacity: 1,
               weight: .8,
               opacity: 1
             });
             platformID = feature.properties.platform.toString();
             marker.bindPopup(feature.properties.html);
             marker.bindTooltip('UGOS Float ' + platformID);
             ugosMarkers.push(marker);
          }
          if(feature.id == 'track') {
            console.log('adding_track');
            var trackStyle = {
              "color": "#FF00FF",
              "opacity": 1,
              "weight": 2
            }
            ugosMarkers.push(L.geoJson(feature, {style: trackStyle}));
          }
        }
      })
      ugosMarkerLayer = L.layerGroup(ugosMarkers);
      ugosMarkerLayer.addTo(map);
    })
  }





function showLastPos(feature, map) {
  console.log("showLastPos()");
  console.log("Using public_name: " + feature.properties.public_name);
  // Check for EEZ Warning and draw red circle around vehicle
  //var eez = feature.properties.eez_early_warning;
  //if (eez) {
  //  lon = feature.geometry.coordinates[0];
  //  lat = feature.geometry.coordinates[1];
  //  var circle = L.circleMarker([lat, lon], {
  //  radius: 25,
  //  color:  'red',
  //  fillOpacity: 0,
  //  weight: 2
  //  });
  //  circle.addTo(gandalfMap);
  //}

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
  bearing = feature.properties.bearing;
  lastPos = L.marker([lat, lon], {icon: currPosIcon, rotationAngle: bearing});
  lastPos.bindPopup(feature.properties.html)
  lastPos.bindTooltip(feature.properties.public_name.toUpperCase());
  lastPos.getPopup().on('add', function() {
    $('#new-dash').hide();
  });
  lastPos.getPopup().on('remove', function() {
    $('#wgLegend').hide();
  });
  lastPos.addTo(map)

  // waypoints smoke 'em if ya got 'em
  if (feature.properties.waypoint_point) {
      wpLon = feature.properties.waypoint_point.coordinates[0];
      wpLat = feature.properties.waypoint_point.coordinates[1];
      wayPoint = L.marker([wpLat, wpLon], {icon: wpIcon}).addTo(map);
      wayPoint.bindPopup(feature.properties.waypoint_html)
      wayPoint.bindTooltip(feature.properties.public_name + " waypoint");
  }
}

function layerOpacity(layer, opacity) {
  layer.setOpacity(opacity);
    // GIBS uses layer so we need to pass 
    if ('layers' in layer.options) { 
	if (layer.options.layers.includes('SST')) {
          document.getElementById("wmsLegend").style.opacity = opacity;
	}
    }
}

function salLayerDepth(elevation) {
  console.log('salLayerDepth(): ' + elevation);
  layer = layersNS.rtofsSalinityLayer;
  layer.wmsParams.elevation=elevation;
  layer.redraw();
  elevation = elevation*-1;
  $("#salDepthWindow").text(elevation+'m');
}

function velLayerDepth(elevation) {
  console.log('velLayerDepth(): ' + elevation);
  layer = layersNS.rtofsVelocityLayer;
  layer.wmsParams.elevation=elevation;
  layer.redraw();
  elevation = elevation*-1;
  $("#velDepthWindow").text(elevation+'m');
}

function tempLayerDepth(elevation) {
  console.log('tempLayerDepth(): ' + elevation);
  layer = layersNS.rtofsTempLayer;
  layer.wmsParams.elevation=elevation;
  layer.redraw();
  elevation = elevation*-1;
  $("#tempDepthWindow").text(elevation+'m');
}

function addSSl(map) {
   var imageUrl = '/gandalf/static/images/ssh.png',
    imageBounds = L.latLngBounds([
        //bounding box to include legends on CCAR image
        [16.65, -98.5],
        [31.90, -79.4]]);
        var sshLayer = L.imageOverlay(imageUrl, imageBounds);
        sshLayer.addTo(map).setOpacity(.75);
        //map.removeLayer(sshLayer);
}

function ucwords (str) {
  str = str.toLowerCase();
  return (str + '').replace(/^([a-z])|\s+([a-z])/g, function ($1) {
  return $1.toUpperCase();
  });
}

// Teleport to location
  function teleport(latitude, longitude, teleport_zoom) {
    gandalfMap.setView([latitude, longitude], 8)
    console.log('teleport');
     $("#new-dash").hide();

  }
// Hycom Ocean Current
  function addHycom(map) {
    console.log('Velocity streamlines...');
    //data_file = "https://geo.gcoos.org/data/hycom/hycom_surface_current.json"
    data_file = "https://gandalf.gcoos.org/data/gandalf/hycom/hycom_surface_current_v2.json"
    //data_file = '/data/gandalf/deployments/geojson/hycom_surface_current.json';
    var hycom = $.getJSON(data_file, function() {
    })
    .done(function() {
      console.log('Loaded velocity streamlines data...')
      var velocityLayer = L.velocityLayer({
        displayValues: true,
        displayOptions: {
          velocityType: 'water',
          displayPosition: 'bottomleft',
          displayEmptyString: 'No water data',
          opacity: .99
        },
        data: hycom.responseJSON,
        minVelocity: 0,
        maxVelocity: 1.5,
        velocityScale: 0.9
      }).addTo(map);
    })
}

function deployPlots(vehicle) {
  console.log('deployPlots() for ' + vehicle);
  config_file = '/data/gandalf/gandalf_configs/vehicles/' + vehicle +'/ngdac/deployment.json';
  config = $.getJSON(config_file, function() {
       })
    .done(function() {
      var vehicle = config.responseJSON.gandalf.public_name.toLowerCase();
      var images = config.responseJSON.gandalf.plots.plot_sensor_list;
      var deployed_plot_dir = config.responseJSON.gandalf.plots.deployed_plot_dir;
      console.log(deployed_plot_dir);
      // Hide away hide away jiggity jig
      // show the pretty pictures
      $("#new-dash").hide();
      $("#map").hide();
      $("#portalMap").hide();
      $("#gLayers").hide();
      // Now we load some images, yo!
      images.forEach(function(element) {
        console.log(element);
        var img = document.createElement("IMG");
        img.src = deployed_plot_dir + "/" + element + ".png?epoch=" + Date.now();
        console.log(img.src);
        $("#plotWrapper").append(img);
      })
      $("#plotWrapper").show();
    })
}

function modComps(png_file) {
  // 2023-09-15
  // For now we only show one image, the 400m image.
  // We will need to modify this code if and when we
  // start showing 1000m images.

  // Hide away hide away jiggity jig and show the pretty picture
  $("#new-dash").hide();
  $("#map").hide();
  $("#portalMap").hide();
  $("#gLayers").hide();
  // Now we load an IMG, yo
  var img = document.createElement("IMG");
  img.src = png_file + "?epoch=" + Date.now();
  img.width = 1200;
  img.height = 600;
  $("#plotWrapper").append(img);
  $("#plotWrapper").show();
}

function deployPlots3D(vehicle) {
  console.log('deployPlots3D() for ' + vehicle);
  config_file = '/data/gandalf/gandalf_configs/' + vehicle +'/ngdac/deployment.json';
  config = $.getJSON(config_file, function() {
       })
    .done(function() {
      var vehicle = config.responseJSON.gandalf.public_name.toLowerCase();
      var images = config.responseJSON.gandalf.plots.plot_sensor_list;
      var deployed_plot_dir = config.responseJSON.gandalf.plots.deployed_plot_dir;
      console.log(deployed_plot_dir);
      // Hide away hide away jiggity jig
      // show the pretty pictures
      $("#new-dash").hide();
      $("#map").hide();
      $("#portalMap").hide();
      $("#plotWrapper3D").show();
      $('#plotLoadingSpinner').show();
      // Now we load some images, yo!
      var numIms = images.length;
      var index = 1;
      images.forEach(function(element) {
        $('#plotWrapper3D').append('<div id=' + element +' class="plot3D"></div>');
        src = deployed_plot_dir + "/" + element + "3D.html";
        $("#" + element).load(src, function(){
          console.log('loading 3D plot source for plot ' + index);
          if (index == numIms) {
            $('#plotLoadingSpinner').hide();
          }
          else {
            index++;
          }
        });
      });
  })
}

function updateSummary() {
  console.log('updateSummary()')
  var data_file = "/data/gandalf/gandalf_configs/deployment_summaries/gandalf_sum_totals.json"
  var summary = $.getJSON(data_file, function() {
  })
  .done(function() {
    console.log('Loaded summary data file');
    $('#sum_deployments').text(summary.responseJSON.deployments);
    $('#sum_km').text(summary.responseJSON.km);
    $('#sum_days').text(summary.responseJSON.days_wet);
  })
}

function updateActiveSummary() {
  console.log('updateActiveSummary()')
  var rowCount = $('#new-dash tr').length + 1;
  var daysWet = 0;
  var index = 0;
  $('#new-dash').find('tr').each(function(rowCount) {
      if (index > 0) {
        daysWet = daysWet + Number(($(this).find("td").eq(8).html()));
        if (index == rowCount) {
          $('#active_deployments').text(rowCount);
          $('#active_days').text(daysWet);
        }
      }
      index+=1;
  })
}

