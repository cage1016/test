var router = require('router');
var mail = require('./mail');
var reports = require('./reports');
var ipwarmup = require('./ipwarmup');

// Add routes to initialize code based on the page the user is on.
new router()
  .case('/mail', mail.init)
  .case('/reports/<name>', reports.init)
  .case('/ipwarmup', ipwarmup.init)
  .case('/ipwarmup/<name>', ipwarmup.init)
  .match(location.pathname);