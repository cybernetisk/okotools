var timers = {};

function timerReset(timer_name) {
  timers[timer_name] = (new Date()).getTime();
}

function timerReport(timer_name, comment) {
  var t = (new Date()).getTime();
  var elapsed = (timer_name in timers) ? t - timers[timer_name] : 'unknown';
   
  Logger.log("timer "+timer_name+" elapsed: "+elapsed+(comment ? " ("+comment+")" : ""));
  timers[timer_name] = (new Date()).getTime();
}

