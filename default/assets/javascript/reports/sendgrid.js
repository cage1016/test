var $ = require('jquery');


function object(o) {
    function F() {
    }

    F.prototype = o;
    return new F();
}

function inheritPrototype(subType, superType) {
    var prototype = object(superType.prototype);
    prototype.constructor = subType;
    subType.prototype = prototype;
}

// sendgrid report object
var Sendgrid = function () {
    this.parameter = {
        date: 1
    };
    this.url = 'nothing';
    this.inputData = [
        {
            key: 'email',
            label: 'Email',
            type: 'email',
            placeholder: 'Email address eg testing@example.com',
            id: 'inputEmail',
            elm:'input'
        },
        {
            key: 'limit',
            label: 'Limit',
            type: 'number',
            placeholder: 'Limit',
            id: 'inputLimit',
            elm:'input'
        }
    ];
};

Sendgrid.prototype.clean = function () {
    for (var key in this.parameter) {
        if (this.parameter[key] === null || this.parameter[key] === undefined) {
            delete this.parameter[key];
        }
        if (typeof this.parameter[key] === 'string') {
            if (this.parameter[key].length === 0) {
                delete this.parameter[key];
            }
        }
    }
};

Sendgrid.prototype.get = function (url) {
    return $.ajax({
        type: 'GET',
        url: '/reports/sendgrid/api/' + url
    });
};

Sendgrid.prototype.set = function (values) {
    if (typeof values !== 'object' || values === null) {
        values = {};
    }

    for (var key in values) {
        this.parameter[key] = values[key];
    }

    this.clean();
    this.url = this.target + '?' + $.param(this.parameter);
};

Sendgrid.prototype.fetch = function () {
    return this.get(this.url);
};

Sendgrid.prototype.removeInputData = function (items) {
    this.inputData = this.inputData.filter(function (el) {
        return items.indexOf(el.key) === -1;
    });
};

//-------------------------------------
// bounces
var Bounces = function () {
    Sendgrid.call(this);
    this.target = 'bounces.get.json';
    this.reportName = 'Bounces';
};

inheritPrototype(Bounces, Sendgrid);
//-------------------------------------
// blocks
var Blocks = function () {
    Sendgrid.call(this);
    this.target = 'blocks.get.json';
    this.reportName = 'Blocks';
};

inheritPrototype(Blocks, Sendgrid);
//-------------------------------------
// invalid Email
var InvalidEmails = function () {
    Sendgrid.call(this);
    this.target = 'invalidemails.get.json';
    this.reportName = 'Invalid Emails';
};

inheritPrototype(InvalidEmails, Sendgrid);
//-------------------------------------
// invalid Email
var Spam = function () {
    Sendgrid.call(this);
    this.target = 'spamreports.get.json';
    this.reportName = 'Spam';
};

inheritPrototype(Spam, Sendgrid);
//-------------------------------------
// Generial Statistics
var GeneralStatistics = function () {
    Sendgrid.call(this);
    this.target = 'stats.get.json';
    this.reportName = 'General Statistics';
    this.parameter.aggregate = 1;
    delete this.parameter.date;

    this.removeInputData('email,limit');
    this.inputData.push({
        key: 'category',
        label: 'Category',
        type: 'text',
        placeholder: 'The category for which to retrieve detailed stats',
        id: 'inputCategory',
        elm:'input'
    });
};

inheritPrototype(GeneralStatistics, Sendgrid);
//-------------------------------------
// Generial Statistics
var AdvanceStatistics = function () {
    Sendgrid.call(this);
    this.target = 'stats.getAdvanced.json';
    this.reportName = 'Advance Statistics';

    this.removeInputData('email,limit');
    this.inputData.push({
        key: 'data_type',
        label: 'Datetype',
        id: 'inputDatetype',
        elm:'select'
    });
};

inheritPrototype(AdvanceStatistics, Sendgrid);

//exports
exports.Bounces = Bounces;
exports.Blocks = Blocks;
exports.InvalidEmails = InvalidEmails;
exports.Spam = Spam;
exports.GeneralStatistics = GeneralStatistics;
exports.AdvanceStatistics = AdvanceStatistics;