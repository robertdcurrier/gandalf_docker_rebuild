//private namespace for layers
var layersNS = {
  gandalfMap: L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/Ocean_Basemap/MapServer/tile/{z}/{y}/{x}", {attribution: "Tiles &copy; Esri &mdash; Sources: GEBCO, NOAA"}, {
    maxZoom: 17,
    maxNativeZoom: 13,
    opacity: 1
  }),
  eezLayer: L.tileLayer.wms("https://geo.vliz.be/geoserver/MarineRegions/wms?", {
    layers: 'eez_boundaries',
    format: 'image/png',
    transparent: true
  }),
  nwsNexrad: L.tileLayer.wms("https://opengeo.ncep.noaa.gov:443/geoserver/conus/conus_bref_qcd/ows?SERVICE=WMS&", {
    layers: 'conus_bref_qcd',
    format: 'image/png',
    transparent: true
  }),
  // AOML Geostrophic currents
  geostrophicLayer : L.tileLayer.wms("https://cwcgom.aoml.noaa.gov/thredds/wms/OCEAN_GEOSTROPHIC_CURRENTS/CURRENTS.nc", {
    layers: 'sea_water_velocity',
    format: 'image/png',
    transparent: 'true'
  }),
  // RTOFS Salinity Layer
  rtofsSalinityLayer : L.tileLayer.wms("https://gandalf.gcoos.org:8443/ncWMS2/wms?", {
    layers: 'RTOFS/salinity',
    format: 'image/png',
    transparent: 'true',
    styles: 'default/seq-BlueHeat'
  }),
  // RTOFS Velocity Layer
  rtofsVelocityLayer : L.tileLayer.wms("https://gandalf.gcoos.org:8443/ncWMS2/wms?", {
    layers: 'RTOFS/water_u:water_v-group',
    format: 'image/png',
    transparent: 'true',
  }),
  // RTOFS SSH Layer
  rtofsSSHLayer : L.tileLayer.wms("https://gandalf.gcoos.org:8443/ncWMS2/wms?", {
    layers: 'RTOFS/surf_el',
    format: 'image/png',
    transparent: 'true',
    styles: 'default/psu-plasma'
  }),
  // Rutgers Depth Avg Currewnts
  rutgersDACLayer : L.tileLayer.wms("https://gandalf.gcoos.org:8443/ncWMS2/wms?", {
    layers: 'DAC_RTOFS/dir_depth_avg',
    format: 'image/png',
    transparent: 'true',
    styles: 'default/psu-plasma'
  }),
  // LSU SST Satellite Layer
  lsuSSTLayer : L.tileLayer.wms("https://gandalf.gcoos.org:8443/ncWMS2/wms?", {
    layers: 'SST/sst',
    format: 'image/png',
    transparent: 'true',
    styles: 'default/x-Sst'
  }),
  // LSU Unmasked SST Satellite Layer
  lsuUnmaskedLayer : L.tileLayer.wms("https://gandalf.gcoos.org:8443/ncWMS2/wms?", {
    layers: 'SST/unmasked_sst',
    format: 'image/png',
    transparent: 'true',
    styles: 'default/x-Sst'
  }),
  hfrLayer6K: L.tileLayer.wms("https://hfrnet-tds.ucsd.edu/thredds/wms/HFR/USEGC/6km/hourly/RTV/HFRADAR_US_East_and_Gulf_Coast_6km_Resolution_Hourly_RTV_best.ncd", {
         layers: 'surface_sea_water_velocity',
         format: 'image/png',
         transparent: true
       }),
  oceanPlatformsLayer : L.tileLayer.wms("https://gis.ngdc.noaa.gov/arcgis/services/GulfDataAtlas/BOEM_DrillingPlatforms/MapServer/WmsServer?",
  {
    layers: '0',
    format: 'image/png',
    transparent: true,
    attribution: "GCOOS-RA, BOEM"
  }),
noaaBagServerLayer: L.tileLayer.wms("https://gis.ngdc.noaa.gov/arcgis/services/web_mercator/nos_hydro_dynamic/MapServer/WMSServer?",
{
  layers: '2',
  format: 'image/png',
  transparent: true,
  attribution: "GCOOS-RA, NOAA"
}),

gebcoGridLayer: L.tileLayer.wms("https://www.gebco.net/data_and_products/gebco_web_services/2022/mapserv?",
{
  layers: 'gebco_latest',
  format: 'image/png',
  transparent: true,
  attribution: "GCOOS-RA, BOEM"
}),
noaaDepthsLayer: L.tileLayer.wms("https://gis.charttools.noaa.gov/arcgis/rest/services/MCS/ENCOnline/MapServer/exts/MaritimeChartService/WMSServer?",
{
  layers: '2',
  format: 'image/png',
  transparent: true
}),
noaaBuoysLayer: L.tileLayer.wms("https://gis.charttools.noaa.gov/arcgis/rest/services/MCS/ENCOnline/MapServer/exts/MaritimeChartService/WMSServer?",
{
  layers: '6',
  format: 'image/png',
  transparent: true
}),

weatherNOAALayer: L.tileLayer.wms("https://mapservices.weather.noaa.gov:443/tropical/services/tropical/NHC_tropical_weather_summary/MapServer/WMSServer?",
{
  layers: '26,27,28',
  format: 'image/png',
  transparent: true
}),


 sstLayer : L.imageOverlay("/data/gandalf/modis/sst.png",
  [[17.9, -98],[30.9, -79]]),
  //
  chlLayer : L.imageOverlay("/data/gandalf/modis/chl.png",
  [[17.9, -98],[30.9, -79]]),
  //
  sstColorBar: L.imageOverlay("/data/gandalf/modis/colorbar_sst_10_to_32.png",
  [[25, -65],[35, -62]])
}
  
// Color Legends
var lsu_sst_legend = "https://gandalf.gcoos.org:8443/ncWMS2/wms?REQUEST=";
lsu_sst_legend += "GetLegendGraphic&PALETTE=default&LAYERS=SST/";
lsu_sst_legend += "sst&STYLES=default/x-Sst";
var lsu_unmasked_legend = "https://gandalf.gcoos.org:8443/ncWMS2/wms?REQUEST=GetLegendGraphic&PALETTE=default&LAYERS=SST/unmasked_sst&STYLES=default/x-Sst"
