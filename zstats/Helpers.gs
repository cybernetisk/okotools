/**
 * Helper function to transpose a array
 * @see https://gist.github.com/femto113/1784503
 */
function transpose(a)
{
  return Object.keys(a[0]).map(function (c) { return a.map(function (r) { return r[c]; }); });
}

/**
 * Helper function to get a specific named range for a specific sheet
 */
function getRangeOnSheet(sheet, rname) {
  var name = sheet.getName();
  //var ts = (new Date()).getTime();
  var ret = sheet.getParent().getRangeByName(name+"!"+rname);
  //Logger.log("getRangeOnSheet for "+rname+": "+((new Date()).getTime()-ts));
  return ret;
}
