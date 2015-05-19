var router = require('router');
var sendmail = require('./sendmail');
var reports = require('./reports');
var ipwarmup = require('./ipwarmup');

// Add routes to initialize code based on the page the user is on.
new router()
  .case('/sendmail', sendmail.init)
  .case('/reports/<name>', reports.init)
  .case('/ipwarmup/<name>', ipwarmup.init)
  .match(location.pathname);