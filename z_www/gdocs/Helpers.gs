/**
 * Helper function to transpose a array
 * @see https://gist.github.com/femto113/1784503
 */
function transpose(a)
{
  return Object.keys(a[0]).map(function (c) { return a.map(function (r) { return r[c]; }); });
}

/**
 * Helper function to get a specific named range for the active sheet
 */
function getRange(rname) {
  return getRangeOnSheet(SpreadsheetApp.getActiveSheet(), rname);
}

/**
 * Helper function to get a specific named range for a specific sheet
 */
function getRangeOnSheet(sheet, rname) {
  var name = sheet.getName();
  return SpreadsheetApp.getActiveSpreadsheet().getRangeByName(name+"!"+rname);
}