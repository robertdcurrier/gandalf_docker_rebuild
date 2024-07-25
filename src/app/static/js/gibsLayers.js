//GIBS layers
//
//Do a 3-day composite of Chlorophyll A
//Return as separate layers
  var msMult = 3600000;
  var gibsDate = new Date();
  // Day 1 (-24)
  var layerDate = new Date(gibsDate - (24*msMult));
  var layerTime = layerDate.toISOString().split('T')[0]
  var gibsMODIS1 = gibsLayer(layerTime);

  // Day 2 (-48)
  layerDate = new Date(gibsDate - (48*msMult))
  layerTime = layerDate.toISOString().split('T')[0]
  var gibsMODIS2 = gibsLayer(layerTime);

  // Day 3 (-72)
  layerDate = new Date(gibsDate - (72*msMult))
  layerTime = layerDate.toISOString().split('T')[0]
  var gibsMODIS3 = gibsLayer(layerTime);

  // Need to make gibsMODIS1-3 a layer group
  var gibsMODIS = L.layerGroup([gibsMODIS1, gibsMODIS2, gibsMODIS3]);
  // SST
  var msMult = 3600000;
  var gibsDate = new Date();
  var layerDate = new Date(gibsDate - (24*msMult));
  var layerTime = layerDate.toISOString().split('T')[0]
  var SSTLayer = gibsSSTLayer(layerTime);


  function gibsLayer(gibsTime) {
    var template =
      '//gibs-{s}.earthdata.nasa.gov/wmts/epsg3857/best/' +
      '{layer}/default/{time}/{tileMatrixSet}/{z}/{y}/{x}.jpg';
      theLayer  = L.tileLayer(template, {
      layer: 'MODIS_Aqua_L2_Chlorophyll_A',
      tileMatrixSet: 'EPSG3857_1km',
      maxZoom: 13,
      maxNativeZoom: 7,
      time: gibsTime,
      tileSize: 256,
      subdomains: 'abc',
      noWrap: true,
      continuousWorld: true,
      // Prevent Leaflet from retrieving non-existent tiles on the
      // borders.
      bounds: [
        [-85.0511287776, -179.999999975],
        [85.0511287776, 179.999999975]
      ],
      attribution:
        '<a href="https://wiki.earthdata.nasa.gov/display/GIBS">' +
        'NASA EOSDIS GIBS</a>&nbsp;&nbsp;&nbsp;' +
        '<a href="https://github.com/nasa-gibs/web-examples/blob/master/examples/leaflet/webmercator-epsg3857.js">' +
        'View Source' +
        '</a>'
    })
    console.log('Adding gibsLayer... ' + theLayer);
    return theLayer;
  }

  function gibsSSTLayer(gibsTime) {
      var template =
        '//gibs-{s}.earthdata.nasa.gov/wms/epsg3857/best/' +
        '{layer}/default/{time}/{tileMatrixSet}/{z}/{y}/{x}.jpg';
        gibsSSTLayer = L.tileLayer(template, {
        layer: 'GHRSST_L4_MUR_Sea_Surface_Temperature',
        tileMatrixSet: 'EPSG3857_1km',
        maxZoom: 13,
        maxNativeZoom: 7,
        time: gibsTime,
        tileSize: 256,
        subdomains: 'abc',
        noWrap: true,
        continuousWorld: true,
        // Prevent Leaflet from retrieving non-existent tiles on the
        // borders.
        bounds: [
          [-85.0511287776, -179.999999975],
          [85.0511287776, 179.999999975]
        ],
        attribution:
          '<a href="https://wiki.earthdata.nasa.gov/display/GIBS">' +
          'NASA EOSDIS GIBS</a>&nbsp;&nbsp;&nbsp;' +
          '<a href="https://github.com/nasa-gibs/web-examples/blob/master/examples/leaflet/webmercator-epsg3857.js">' +
          'View Source' +
          '</a>'
      })
      return gibsSSTLayer;
    }
