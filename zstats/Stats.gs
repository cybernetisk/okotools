function onOpen() {
  var s = SpreadsheetApp.getActiveSpreadsheet();

  // add menu entries
  s.addMenu("Z-statistikk", [
    {
      name: "Synkroniser siste rapporter",
      functionName: "reloadLatestZs"
    },
    {
      name: "Velg Z som lastes på nytt",
      functionName: "reloadZ"
    },
    {
      name: "Tving oppdatering av regnearket",
      functionName: "forceRecalc"
    },
    {
      name: "Last rapporter som mangler",
      functionName: "loadMissingReports"
    }
  ]);
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

    var d = getZDataByCache(sheet.getSheetId());
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
}


function reloadLatestZs() {
  var r = SpreadsheetApp.getActiveSpreadsheet().getSheetByName("Enkeltvis data").getRange(1, 2);
  var numberOfReportsToReload = 4;

  var sheets = getZSheetList();
  for (var i = 0; i < sheets.length && i < numberOfReportsToReload; i++) {
    var sheet = sheets[i];
    cacheInvalidate('z', sheet.getSheetId());
    cacheInvalidate('zdate', sheet.getSheetId());
    getZData(sheet);
    Logger.log("reloaded sheet "+sheet.getSheetId());

    r.setValue((r.getValue() || 0) + 1);
  }

  forceRecalc();
}


function isValidSheetName(sheetName) {
  // make sure we ignore certain sheets
  // we are only interested in real Zs
  var p = /[0-9]/; // all real Z should contain a number
  return p.test(sheetName) && sheetName.substring(0, 2) !== "X:";
}


function getZSheetList() {
  var sheet_id = SpreadsheetApp.getActiveSpreadsheet().getRangeByName("datasheet_id").getValue();
  var sh = SpreadsheetApp.openById(sheet_id);
  var sheets = sh.getSheets();
  var list = [];

  for (var i in sheets) {
    var sheet = sheets[i];
    if (isValidSheetName(sheet.getName())) {
      list.push(sheet);
    }
  }

  return list;
}


function getZSheetIdsInRange(dateFrom, dateTo) {
  var timeFrom = dateFrom.getTime();
  var timeTo = dateTo.getTime();

  var sheetIds = [];
  var sheetTimes = {};

  var sheetDates = getCacheTable('zdate');
  for (var sheetId in sheetDates) {
    var sheetTime = new Date(sheetDates[sheetId]).getTime();
    if (sheetTime >= timeFrom && sheetTime <= timeTo) {
      sheetIds.push(sheetId);
      sheetTimes[sheetId] = sheetTime;
    }
  }

  return sheetIds.sort(function (a, b) {
    return sheetTimes[b] - sheetTimes[a];
  });
}


function loadMissingReports() {
  var max_to_load = 20;
  var loaded_i = 0;

  getZSheetList().forEach(function (sheet) {
    if (getZDateByCache(sheet.getSheetId()) !== null) {
      return;
    }

    if (loaded_i == max_to_load) {
      return;
    }

    loaded_i++;

    getZData(sheet);
    Logger.log('loaded data for sheet ' + sheet.getSheetId());
  });

  forceRecalc();
}


/**
 * Generate data from all Zs
 */
function getZDataDetails() {
  var datasets = [];
  var debetlist = [];
  var kreditlist = [];

  var dateFrom = SpreadsheetApp.getActiveSpreadsheet().getRangeByName("date_from").getValue();
  var dateTo = SpreadsheetApp.getActiveSpreadsheet().getRangeByName("date_to").getValue();
  var sheetIds = getZSheetIdsInRange(dateFrom, dateTo);

  sheetIds.map(function (sheetId) {
    var data = getZDataByCache(sheetId);
    if (data === null) {
      return;
    }

    data['debetmap'] = {};
    data['kreditmap'] = {};
    data['salestotal'] = 0;

    data['debet'].forEach(function (account) {
      var id = account[0] + " " + account[1];
      if (debetlist.indexOf(id) == -1) {
        debetlist.push(id);
      }

      data['debetmap'][id] = account[2];
    });

    data['sales'].forEach(function (account) {
      var id = account[0] + " " + account[1];
      if (kreditlist.indexOf(id) == -1) {
        kreditlist.push(id);
      }

      data['kreditmap'][id] = account[2];
      data['salestotal'] += account[2];
    });

    datasets.push(data);
  });

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
  kreditlist.forEach(function (text) {
    headings.push('  ' + text);
  });
  headings.push('Totalt salg');
  headings.push('');
  headings.push('Debet-kontoer');
  debetlist.forEach(function (text) {
    headings.push('  ' + text);
  });
  ret.push(headings);

  timerReport('getzstats', 'before data items');

  datasets.forEach(function (data) {
    var d = [];
    d.push(data['sheetid']);
    d.push(data['z']);
    d.push(getZDateByCache(data['sheetid']));
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

    kreditlist.forEach(function (id) {
      d.push(data['kreditmap'][id]);
    });
    d.push(data['salestotal']);

    d.push('');
    d.push('');

    debetlist.forEach(function (id) {
      d.push(data['debetmap'][id]);
    });

    ret.push(d);
    timerReport('getzstats', 'data item parsed');
  });

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

  datasets.forEach(function (data) {
    timerReport('zdataset', 'loop start');
    var date = getZDateByCache(data['sheetid']);
    var date2 = new Date(date);
    var i;

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

    var cash_list = [1, 5, 10, 20, 50, 100, 200, 500, 1000];
    for (i = 0; i < data['cash']['start'].length; i++) {
      genRow("3 Kontantvalør (antall)", cash_list[i], data['cash']['end'][i] - data['cash']['start'][i]);
    }

    debetlist.forEach(function (id) {
      if (id in data['debetmap'])
        genRow("2 Debet", id, data['debetmap'][id]);
    });

    kreditlist.forEach(function (id) {
      if (id in data['kreditmap'])
        genRow("1 Kredit", id, data['kreditmap'][id]);
    });

    genRow("0 Stats", "Antall Z", 1);
  });

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
