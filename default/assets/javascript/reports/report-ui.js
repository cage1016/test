/*jshint -W043 */

var $ = require('jquery');
require('jquery-tmpl');
var React = require('react');
var daterangePicker = require('./daterange-picker');
var Reactable = require('reactable').Table;
var Json2csv = require('./json2csv');

var alertTmpl = '\
    <div class="bs-callout bs-callout-info alert">\
    <h4>Result (${count})</h4>\
    <p></p>\
    </div>';

var inputTmpl = '\
        <div id="${key}-container" class="form-group input-container">\
            <label class="sr-only" for="inputCategory">${label}</label>\
            <input type="${type}" class="form-control input-large" id="${id}" placeholder="${placeholder}">\
        </div>';

var dropDownTmpl = '<div id="${key}-container" class="form-group input-container">\
            <label class="sr-only" for="inputCategory">${label}</label>\
            <select id="${id}" class="form-control">\
                <option value="browsers">Browsers</option>\
                <option value="clients">Clients</option>\
                <option value="devices">Devices</option>\
                <option value="geo">Geo</option>\
                <option value="global">Global</option>\
                <option value="isps">Isp</option>\
            </select>\
        </div>';

var ReportUI = function (report) {
    this.init.apply(this, arguments);

    this.flattenContent = 'noting';
};

ReportUI.prototype.init = function (report) {
    // property
    this.report = report;

    // daterangepicker init
    daterangePicker.init('daterange');

    $(function () {

        // page title
        $('#report-name').text(report.reportName);

        // prepare report input box
        this.prepareInputBox();

        // addHander
        this.addHandler();

    }.bind(this));
};

ReportUI.prototype.prepareInputBox = function () {
    var inputArray = [];
    $.map(this.report.inputData, function (data, index) {
        if (data.elm === 'input') {
            inputArray.push($.tmpl(inputTmpl, data).data('key', data.key));
        }
        if (data.elm === 'select') {
            inputArray.push($.tmpl(dropDownTmpl, data).data('key', data.key));
        }
    }.bind(this));

    $('#report-form > div:nth-child(1)').after(inputArray);
};

ReportUI.prototype.collectionInputBoxValue = function () {
    var result = {};
    var inputContainers = $('#report-form .input-container');
    $.map(inputContainers, function (inputContainer, index) {
        var $this = $(inputContainer);
        result[$this.data('key')] = $($this.children().get(1)).val();
    }.bind(this));

    return result;
};

ReportUI.prototype.alert = function () {

    function show(values, contentLength) {
        var disp = [];

        disp.push(jQuery('<div/>', {
            text: 'date range: ' + values.start_date + ' - ' + values.end_date
        }));
        for (var key in values) {
            if (key !== 'start_date' && key !== 'end_date') {
                disp.push(jQuery('<div/>', {
                    text: key + ': ' + values[key]
                }));
            }
        }

        var buf = $(alertTmpl).clone();
        buf = buf.find('p').append(disp).end();
        $.extend(values, {
            count: contentLength
        });

        $.tmpl(buf[0].outerHTML, values).prependTo('#result');
    }

    function hide() {
        $('#result').html('');
    }

    return {
        show: show,
        hide: hide
    };
};

ReportUI.prototype.addHandler = function () {
    var $download = $('#btn-download-csv');
    var $btnSearch = $('#btn-search');

    $('#btn-search').on('click', function () {
        var values = {
            'start_date': daterangePicker.dateRange.start,
            'end_date': daterangePicker.dateRange.end
        };
        $.extend(values, this.collectionInputBoxValue());
        this.report.set(values);

        $btnSearch.html('<span class="glyphicon glyphicon-search"></span> Search...');

        this.report.fetch().done(function (data) {
            $btnSearch.html('<span class="glyphicon glyphicon-search"></span> Search');

            var content = JSON.parse(data);
            if (!$.isArray(content)) {
                var buf = [];
                buf.push(content);
                content = buf;
            }

            var contentLength = content.length;

            if (contentLength) {
                var header = [];
                for (var key in content[0]) {
                    header.push(content[0][key]);
                }

                this.flattenContent = Json2csv.flatten(content);

                React.renderComponent(
                    React.createElement(Reactable, {
                        className: 'table',
                        data: this.flattenContent,
                        itemsPerPage: 25,
                        sortable: header
                    }),
                    document.getElementById('result')
                );
            } else {
                this.alert().hide();
            }
            this.alert().show(values, contentLength);
        }.bind(this));

    }.bind(this));

    $download.on('click', function () {
        //var values = {
        //    'start_date': daterangePicker.dateRange.start,
        //    'end_date': daterangePicker.dateRange.end
        //};
        //$.extend(values, this.collectionInputBoxValue());
        //this.report.set(values);

        var csv = Json2csv.convert(this.flattenContent);

        this.downloadFile('2.csv', 'data:text/csv;charset=UTF-8,' + encodeURIComponent(csv));

        //window.location.href = '/reports/sendgrid/donwload/' + this.report.url;
    }.bind(this));
};

ReportUI.prototype.downloadFile = function (fileName, urlData) {
    var aLink = document.createElement('a');
    var evt = document.createEvent('HTMLEvents');
    evt.initEvent('click');
    aLink.download = fileName;
    aLink.href = urlData;
    aLink.dispatchEvent(evt);
};

module.exports = ReportUI;