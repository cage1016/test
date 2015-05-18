var $ = require('jquery');
var moment = require('moment');
require('bootstrap-daterangepicker');
require('bootstrap');


var exports = module.exports;

exports.dateRange = null;

exports.init = function (dom_id) {
    this.addDaterangePickerHandler(dom_id);
};

exports.addDaterangePickerHandler = function (dom_id) {
    var $daterangePicker = $('#' + dom_id);
    var $daterangeSpan = $('#' + dom_id + ' span');

    $(function () {
        // initialize default display daterange is today
        var format = 'YYYY-MM-DD';
        $daterangeSpan.html(moment().format(format) + ' - ' + moment().format(format));

        exports.dateRange = {
            'start': moment().format(format),
            'end': moment().format(format)
        };

        // initialize daterangepicker
        $daterangePicker.daterangepicker(
            {
                ranges: {
                    'Today': [new Date(), new Date()],
                    'Yesterday': [moment().subtract('days', 1), moment().subtract('days', 1)],
                    'Last 7 Days': [moment().subtract('days', 6), new Date()],
                    'Last 30 Days': [moment().subtract('days', 29), new Date()],
                    'This Month': [moment().startOf('month'), moment().endOf('month')],
                    'Last Month': [moment().subtract('month', 1).startOf('month'), moment().subtract('month', 1).endOf('month')]
                },
                opens: 'right',
                format: format
            },
            function (start, end) {
                $daterangeSpan.html(start.format(format) + ' - ' + end.format(format));

                exports.dateRange = {
                    'start': start.format(format),
                    'end': end.format(format)
                };
            }
        );
    }.bind(this));
};
