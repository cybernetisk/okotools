
function getZDateByCache(sheetId) {
  var cached = getCacheValue('zdate', sheetId);
  if (cached !== null) {
    return new Date(cached);
  }
}

function getZDataByCache(sheetId) {
  return getCacheValue('z', sheetId);
}

/**
 * Get date for a Z-report
 */
function getZDate(sheet) {
  cached = getRangeOnSheet(sheet, "Zdato").getValue();
  setCacheValue('zdate', sheet.getSheetId(), cached);
  return new Date(cached);
}

/**
 * Generate data for a specific Z-sheet
 */
function getZData(sheet) {
  /**
   * For sales and debet, select the valid columns.
   * The data should be [account-info, description, value]
   */
  function getSalesAndDebetRows(data) {
    var newdata = [];
    for (var x in data) {
      if (data[x][0] != "" && data[x][4] != "") {
        newdata.push([data[x][0], data[x][1], data[x][4]]);
      }
    }
    return newdata;
  }
  function getSales(sheet) {
    return getSalesAndDebetRows(getRangeOnSheet(sheet, "K_G1").getValues());
  }
  function getDebet(sheet) {
    return getSalesAndDebetRows(getRangeOnSheet(sheet, "D_G1").getValues());
  }
  
  /**
   * Extract first column from a data set
   */
  function getFirstCol(data) {
    var newdata = [];
    for (x in data) {
      newdata.push(data[x][0]);
    }
    return newdata;
  }
  
  /**
   * Get dayname from daynumber
   */
  function getWeek(val) {
    var day = Utilities.formatDate(val, "Europe/Oslo", "u");
    return ["Mandag", "Tirsdag", "Onsdag", "Torsdag", "Fredag", "Lørdag", "Søndag"][day-1];
  }
  
  Logger.log("Check sheet: "+sheet.getName());
  
  /**
   * Build data
   */
  var dateObj = new Date(getRangeOnSheet(sheet, "Zdato").getValue());
  var data = {
    "sheetid": sheet.getSheetId(),
    "z": getRangeOnSheet(sheet, "Znr").getValue(),
    "age": (new Date().getTime() - (new Date(getRangeOnSheet(sheet, "Zdato").getValue()).getTime()))/86400000,
    "date": getWeek(dateObj)+" "+Utilities.formatDate(dateObj, "Europe/Oslo", "dd.MM.YYYY"),
    //"builddate": Utilities.formatDate(new Date(), "Europe/Oslo", "dd.MM.YYYY HH:mm"),
    "responsible": getRangeOnSheet(sheet, "Ansvarlig").getValue(),
    "type": getRangeOnSheet(sheet, "Arrtype").getValue(),
    "cash": {
      "start": getFirstCol(getRangeOnSheet(sheet, "AntallStart").getValues()),
      "end": getFirstCol(getRangeOnSheet(sheet, "AntallSlutt").getValues())
    },
    "sales": getSales(sheet),
    "debet": getDebet(sheet)
  };

  setCacheValue('z', data['sheetid'], data);
  setCacheValue('zdate', data['sheetid'], dateObj);

  return data;
}
