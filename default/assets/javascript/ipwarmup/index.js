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
var DetailScheduleApp = require('../share/detailScheduleApp');

module.exports = {
  init: function (args) {
    args = args || '';
    var action = args.split('/')[0];

    switch (action) {
      case 'resource':

        React.render(<UploadApp bucketName={'cage-20160705-edm.appspot.com'} objectNamePerfix={'ipwarmup'}/>,
          document.getElementById('uploadApp')
        );

        break;
      case 'new':

        React.render(<AddScheduleApp header={'Add IP Warmup Schedule'} type={'ipwarmup'}/>,
          document.getElementById('add-ip-warmup-schedule')
        );

        break;
      case 'detail':

        var id = args.split('/')[1];

        React.render(<DetailScheduleApp id={id}/>,
          document.getElementById('detail-schedule')
        );

        break;
      default :

        React.render(<ListIPWarmupScheduleApp/>,
          document.getElementById('list-ip-warmup-schedule')
        );
    }


  }
};