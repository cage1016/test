/** @jsx React.DOM */

/*jshint browser: true */
/*jslint node: true */
/*jshint -W109*/
/*jshint -W108*/

'use strict';

var React = require('react');
var UploadApp = require('./uploadApp');

module.exports = {
  init: function (action) {


    React.render(<UploadApp insertUrl={"/api/recipient/insert"}/>,
      document.getElementById('uploadApp')
    );

  }
};