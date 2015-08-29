var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('Cache');
var caches = {};
_initCache();


function getCacheTable(table_name) {
  if (!(table_name in caches)) {
    return null;
  }

  var dataColumn = 1;
  var flat = {};
  for (var key_name in caches[table_name]) {
    flat[key_name] = caches[table_name][key_name][dataColumn];
  }
  return flat;
}

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
    var row_i = _getFreeRow();
    caches[table_name][key_name] = [row_i, null];
    rowsUsed[row_i] = true;
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

  delete rowsUsed[caches[table_name][key_name][0]];
  delete caches[table_name][key_name];
}


function _initCache() {
  caches = {};
  rowsUsed = {};
  var data = sheet.getDataRange().getValues();

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
  rowsUsed[row_i] = true;
}

function _getFreeRow() {
  var i;
  var lastRow = sheet.getLastRow();
  for (i = 0; i < lastRow; i++) {
    if (rowsUsed[i] !== true) {
      break;
    }
  }

  return i;
}


function cacheTest() {
  Logger.log(setCacheValue('z', '2102053375', 'something'));
}
