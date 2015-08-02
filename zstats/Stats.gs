function onOpen() { 
  var s = SpreadsheetApp.getActiveSpreadsheet();
  
  // add menu entries
  s.addMenu("Z-statistikk", [
    {
      name: "Oppdater data",
      functionName: "refreshData"
    },
    {
      name: "Last Z på nytt",
      functionName: "reloadZ"
    },
    {
      name: "Tving oppdatering",
      functionName: "forceRecalc"
    }
  ]);
}

function refreshData() {
  getZDataDetails(true);
}

function reloadZ() {
  var x = Browser.inputBox("Skriv inn enten Z-nr eller sheet-id på Z-rapporten");
  var found;
  
  var sheets = getZSheetList();
  for (var sheet_i in sheets) {
    var sheet = sheets[sheet_i];
    
    if (sheet.getSheetId() == x) {
      found = sheet;
      break;
    }
    
    var d = getZData(sheet, true);
    if (d !== null && d['z'] == x) {
      found = sheet;
      break;
    }
  }
  
  if (!found) {
    Browser.msgBox("Fant ikke Z-rapport!");
    return;
  }
  
  cacheInvalidate('z', found.getSheetId());
  cacheInvalidate('zdate', found.getSheetId());
  getZData(found);
  Browser.msgBox("Data oppdatert");
  return;
}


function reloadLatestZs() {
  var r = SpreadsheetApp.getActiveSpreadsheet().getSheetByName("Enkeltvis data").getRange(1, 2);
  
  // reload first 3 Zs
  var sheets = getZSheetList();
  for (var i = 0; i < sheets.length && i < 4; i++) {
    var sheet = sheets[i];
    cacheInvalidate('z', sheet.getSheetId());
    cacheInvalidate('zdate', sheet.getSheetId());
    getZData(sheet);
    Logger.log("reloaded sheet "+sheet.getSheetId());
    
    r.setValue((r.getValue() || 0) + 1);
  }
    
  refreshData();
}


function getId() {
  Logger.log(SpreadsheetApp.getActiveSpreadsheet().getId());
}

/**
 * Generate a list of all sheets that are expected to be real Z
 * that goes into the accounting
 */
function getZSheetList() {
  var sheet_id = SpreadsheetApp.getActiveSpreadsheet().getRangeByName("datasheet_id").getValue();
  var sh = SpreadsheetApp.openById(sheet_id);
  Logger.log(sh.getName());
  var sheets = sh.getSheets();
  var list = [];
  
  for (var i in sheets) {
    var sheet = sheets[i];
    var name = sheet.getName();
    
    // make sure we ignore certain sheets
    // we are only interested in real Zs
    //if (name == "MAL" || name == "Statistikk" || name.substring(0, 2) == "X:")
    var p = /[0-9]/; // all real Z should contain a number
    if (!p.test(name) || name.substring(0, 2) == "X:")
      continue;
    
    list.push(sheet);
  }
  
  return list;
}

/**
 * Generate data from all Zs
 */
function getZDataDetails(dont_force_cache)
{
  var force_cache = !dont_force_cache;
  var sheets = getZSheetList();
  var datasets = [];
  var debetlist = [];
  var kreditlist = [];syn
  
  var date_from = SpreadsheetApp.getActiveSpreadsheet().getRangeByName("date_from").getValue().getTime()
  var date_to   = SpreadsheetApp.getActiveSpreadsheet().getRangeByName("date_to").getValue().getTime()
  
  // create data for the "view"
  var time_start = (new Date()).getTime();
  for (var sheet_i in sheets) {
    var elapsed_total = (new Date()).getTime() - time_start;
    if (elapsed_total > 300000) continue; // max "running time"
    
    var sheet = sheets[sheet_i];
    
    // check if inside date range
    var t = getZDate(sheet, force_cache);
    if (t === null) continue;
    t = t.getTime();
    if (!isNaN(t) && (t < date_from || t > date_to)) continue;
    
    var data = getZData(sheet, force_cache);
    if (data === null) continue;
    
    data['sheet'] = sheet;
    data['debetmap'] = {};
    data['kreditmap'] = {};
    data['salestotal'] = 0;
    
    // mapping of debets
    for (var i in data['debet']) {
      var d = data['debet'][i];
      var id = d[0]+" "+d[1];
      if (debetlist.indexOf(id) == -1) {
        debetlist.push(id);
      }
      
      data['debetmap'][id] = d[2];
    }
    
    // mapping of kredits
    for (var i in data['sales']) {
      var d = data['sales'][i];
      var id = d[0]+" "+d[1];
      if (kreditlist.indexOf(id) == -1) {
        kreditlist.push(id);
      }
      
      data['kreditmap'][id] = d[2];
      data['salestotal'] += d[2];
    }
    
    datasets.push(data);
  }
  
  //SpreadsheetApp.getActiveSpreadsheet().toast("Data parsing complete", "Z-parser", 2);
  
  debetlist.sort();
  kreditlist.sort();
  
  return {
    'datasets': datasets,
    'debetlist': debetlist,
    'kreditlist': kreditlist
  };
}

/**
 * Generate a "magic" array of data from the Zs
 * that can be pulled straight to the spreadsheet itself
 * for easier statistical analysis and presentation/validation of data
 */
function getZStats() {
  timerReset('getzstats-total');
  timerReset('getzstats');
  
  var x = getZDataDetails();
  var datasets = x['datasets'];
  var debetlist = x['debetlist'];
  var kreditlist = x['kreditlist'];
  
  timerReport('getzstats', 'data loaded');
  
  // create the "view"
  var ret = [];
  
  var headings = [];
  headings.push('ID');
  headings.push('Z');
  headings.push('Dato');
  headings.push('Ansvarlig');
  headings.push('Type');
  headings.push('');
  headings.push('Endring kontanter (antall)');
  headings.push('1');
  headings.push('5');
  headings.push('10');
  headings.push('20');
  headings.push('50');
  headings.push('100');
  headings.push('200');
  headings.push('500');
  headings.push('1000');
  headings.push('');
  headings.push('Kredit-kontoer');
  for (var i = 0; i < kreditlist.length; i++) {
    headings.push('  '+kreditlist[i]);
  }
  headings.push('Totalt salg');
  headings.push('');
  headings.push('Debet-kontoer');
  for (var i = 0; i < debetlist.length; i++) {
    headings.push('  '+debetlist[i]);
  }
  ret.push(headings);
  
  timerReport('getzstats', 'before data items');
  
  for (var data_i in datasets) {
    
    var data = datasets[data_i];
    
    var d = [];
    d.push(data['sheet'].getSheetId());
    d.push(data['z']);
    d.push(getZDate(data['sheet']));
    d.push(data['responsible']);
    d.push(data['type']);
    d.push('');
    d.push('');
    
    // cash
    for (var i = 0; i < data['cash']['start'].length; i++) {
      d.push(data['cash']['end'][i] - data['cash']['start'][i]);
    }
    
    d.push('');
    d.push('');
    
    // kredits
    for (var i in kreditlist) {
      var id = kreditlist[i];
      
      d.push(data['kreditmap'][id]);
    }
    d.push(data['salestotal']);
    
    d.push('');
    d.push('');
    
    // debets
    for (var i in debetlist) {
      var id = debetlist[i];
      
      d.push(data['debetmap'][id]);
    }
    
    ret.push(d);
    timerReport('getzstats', 'data item parsed');
  }
  
  timerReport('getzstats-total');
  if (ret.length == 0) return [['']];
  return ret;
}

/**
 * Generate a row-based data-report of Zs
 */
function getZDataset() {
  timerReset('zdataset');
  var x = getZDataDetails();
  var datasets = x['datasets'];
  var debetlist = x['debetlist'];
  var kreditlist = x['kreditlist'];
  
  timerReport('zdataset', 'got data');
  
  // create the "view"
  var ret = [];
  ret.push([
    'Znr',
    'Dato',
    'År',
    'Måned',
    'Dag',
    'Ansvarlig',
    'Type',
    'Feltkategori',
    'Felt',
    'Verdi',
    'Uke'
  ]);
  
  var i = 0;
  for (var data_i in datasets) {
    timerReport('zdataset', 'loop start');
    var data = datasets[data_i];
    var date = getZDate(data['sheet']);
    var date2 = new Date(date);
    
    function genRow(cat, name, value) {
      var d = [];
      d.push(data['z']);
      d.push(date);
      d.push(Utilities.formatDate(date2, "Europe/Oslo", "yyyy"));
      d.push(Utilities.formatDate(date2, "Europe/Oslo", "MM-MMM"));
      d.push(Utilities.formatDate(date2, "Europe/Oslo", "dd"));
      d.push(data['responsible']);
      d.push(data['type']);
      d.push(cat);
      d.push(name);
      d.push(value);
      d.push(Utilities.formatDate(date2, "Europe/Oslo", "YYYY-ww"));
      ret.push(d);
    }
    
    // cash
    var cash_list = [1, 5, 10, 20, 50, 100, 200, 500, 1000];
    for (var i = 0; i < data['cash']['start'].length; i++) {
      genRow("3 Kontantvalør (antall)", cash_list[i], data['cash']['end'][i] - data['cash']['start'][i]);
    }
    
    // debets
    for (var i in debetlist) {
      var id = debetlist[i];
      if (id in data['debetmap'])
        genRow("2 Debet", id, data['debetmap'][id]);
    }
    
    // kredits
    for (var i in kreditlist) {
      var id = kreditlist[i];
      if (id in data['kreditmap'])
        genRow("1 Kredit", id, data['kreditmap'][id]);
    }
    
    genRow("0 Stats", "Antall Z", 1);
  }
  
  timerReport('zdataset');
  return ret;
}

/**
 * Force recalculation
 */
function forceRecalc() {
  SpreadsheetApp.flush();
  //var x = transpose(getZStats());
  //Logger.log("hm");
}
