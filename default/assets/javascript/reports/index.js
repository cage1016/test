var sendgrid = require('./sendgrid');
var Report = require('./report-ui');

module.exports = {
    init: function (reportName) {

        switch (reportName) {
            case 'bounces':
                new Report(new sendgrid.Bounces());
                break;
            case 'blocks':
                new Report(new sendgrid.Blocks());
                break;
            case 'invaid_emails':
                new Report(new sendgrid.InvalidEmails());
                break;
            case 'spam':
                new Report(new sendgrid.Spam());
                break;
            case 'statistics':
                new Report(new sendgrid.GeneralStatistics());
                break;
            case 'advance_statistics':
                new Report(new sendgrid.AdvanceStatistics());
                break;
            default :
                console.log('not any route found!');
        }
    }
};