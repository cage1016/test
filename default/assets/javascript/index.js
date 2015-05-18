var router = require('router');
var sendmail = require('./sendmail');
var reports = require('./reports');

// Add routes to initialize code based on the page the user is on.
new router()
    .case('/sendmail', sendmail.init)
    .case('/reports/<name>', reports.init)
    .match(location.pathname);