/*var caches = {};

function getCacheValue(cache_name, sheet_id) {
  if (!(cache_name in caches)) {
    caches[cache_name] = _getCache(cache_name);
  }
  
  if (caches[cache_name] != null) {
    if (sheet_id in caches[cache_name]) {
      return caches[cache_name][sheet_id];
    }
  }
  
  return null;
}

function setCacheValue(cache_name, sheet_id, object) {
  if (!(cache_name in caches)) {
    caches[cache_name] = _getCache('z-dates');
  }
  if (caches[cache_name] == null) {
    caches[cache_name] = {};
  }
  
  caches[cache_name][sheet_id] = object;
  
  var cache = CacheService.getDocumentCache();
  cache.put(cache_name, JSON.stringify(caches[cache_name]), 21600);
}

function _getCache(name) {
  var cache = CacheService.getDocumentCache();
  val = cache.get(name);
  if (val != null) {
    val = JSON.parse(val);
  }
  
  return val;
}*/
