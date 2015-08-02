/**
 * @OnlyCurrentDoc
 * (makes the "app auth" only give access to this document, not the whole Google Disk)
 */

var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('Cache');
var next_free = 0;
var caches = {};
_initCache();


function getCacheValue(table_name, key_name) {
  if (!(table_name in caches)) {
    return null;
  }
  
  if (key_name in caches[table_name]) {
    return caches[table_name][key_name][1];
  }
  
  return null;
}


function setCacheValue(table_name, key_name, object) {
  if (!(table_name in caches)) {
    caches[table_name] = {};
  }
  
  if (!(key_name in caches[table_name])) {
    caches[table_name][key_name] = [next_free++, null];
  }
  
  caches[table_name][key_name][1] = object;
  
  sheet.getRange(caches[table_name][key_name][0]+1, 1, 1, 4).setValues([[
    table_name,
    key_name,
    JSON.stringify(object),
    new Date()
  ]]);
}


function cacheInvalidate(table_name, key_name) {
  if (!(table_name in caches)) {
    return;
  }
  
  if (!(key_name in caches[table_name])) {
    return;
  }
  
  
  sheet.getRange(caches[table_name][key_name][0]+1, 1, 1, 4).setValues([[
    '',
    '',
    '',
    ''
  ]]);
  
  delete caches[table_name][key_name];
}


function _initCache() {
  caches = {};
  var data = sheet.getDataRange().getValues();
  next_free = data.length;
  
  for (var y = 0; y < data.length; y++) {
    _addToCache(data[y][0], data[y][1], data[y][2], y);
  }
}

function _addToCache(table_name, key_name, json, row_i) {
  if (table_name == "" || key_name == "") return;
  if (!(table_name in caches)) {
    caches[table_name] = {};
  }
  caches[table_name][key_name] = [row_i, JSON.parse(json)];
}



function cacheTest() {
  Logger.log(setCacheValue('z', '2102053375', 'something'));
}
