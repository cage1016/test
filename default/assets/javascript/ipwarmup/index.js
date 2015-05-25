/** @jsx React.DOM */

/*jshint browser: true */
/*jslint node: true */
/*jshint -W109*/
/*jshint -W108*/

'use strict';

var React = require('react');
var UploadApp = require('../share/uploadApp');
var AddScheduleApp = require('../share/addScheduleApp');
var ListIPWarmupScheduleApp = require('../share/listIPWarmupScheduleApp');

module.exports = {
  init: function (action) {

    switch (action) {
      case 'resource':

        React.render(<UploadApp bucketName={'cheerspoint-recipient'} objectNamePerfix={'ipwarmup'}/>,
          document.getElementById('uploadApp')
        );

        break;
      case 'new':

        React.render(<AddScheduleApp header={'Add IP Warmup Schedule'} type={'ipwarmup'}/>,
          document.getElementById('add-ip-warmup-schedule')
        );

        break;
      default :

        React.render(<ListIPWarmupScheduleApp/>,
          document.getElementById('list-ip-warmup-schedule')
        );
    }


  }
};