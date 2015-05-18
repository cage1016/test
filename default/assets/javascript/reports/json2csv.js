var $ = require('jquery');
require('jquery-csv');

var Json2Csv = function () {
    // https://github.com/konklone/json
};

Json2Csv.prototype.flatten = function (json) {
    var inArray = this.arrayFrom(json);

    var outArray = [];
    for (var row in inArray)
        outArray[outArray.length] = this.parseObject(inArray[row]);

    return outArray;
};

Json2Csv.prototype.convert = function (outArray) {
    return $.csv.fromObjects(outArray);
};

Json2Csv.prototype.arrayFrom = function (json) {
    var queue = [], next = json;
    while (next) {
        if ($.type(next) == 'array')
            return next;
        for (var key in next)
            queue.push(next[key]);
        next = queue.shift();
    }
    // none found, consider the whole object a row
    return [json];
};

Json2Csv.prototype.parseObject = function (obj, path) {
    if (path === undefined)
        path = '';

    var type = $.type(obj);
    var scalar = (type == 'number' || type == 'string' || type == 'boolean' || type == 'null');

    var d = {};
    if (type == 'array' || type == 'object') {
        for (var i in obj) {

            var newD = this.parseObject(obj[i], path + i + '/');
            $.extend(d, newD);
        }

        return d;
    }

    else if (scalar) {
        var endPath = path.substr(0, path.length - 1);
        d[endPath] = obj;
        return d;
    }

    // ?
    else return {};
};

module.exports = new Json2Csv();