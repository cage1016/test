/** @jsx React.DOM */

/*jshint browser: true */
/*jslint node: true */
/*jshint -W109*/
/*jshint -W108*/

'use strict';

var React = require('react');
var $ = require('jquery');
var Spinner = require('./vitullo-spinner.jsx');
var moment = require('moment');
require('eonasdan-bootstrap-datetimepicker');
require('bootstrap');

var addIPWarmupScheduleApp = React.createClass({

  mixins: [
    // Load the spinner mixin.
    // http://facebook.github.io/react/docs/reusable-components.html#mixins
    Spinner.Mixin
  ],

  getInitialState: function () {
    return {
      recipient: {},
      recipientTxtUrlsafe: '',
      recipientEdmUrlsafe: '',
      category: '',
      scheduleDuration: 1,
      ipCounts: 1,
      startTime: '',
      recipientSkip: 0,
      hourRate: 24,
      type: this.props.type,
      subject: '',
      senderEmail: '',
      senderName: ''
    };
  },

  txtfilter: function (r) {
    return r.content_type === 'text/csv';
  },

  edmfilter: function (r) {
    return r.content_type === 'text/html';
  },

  fetchRecipient: function () {
    this.startSpinner('spinner');
    $.get('/api/recipient', function (data) {
      this.stopSpinner('spinner');
      this.setState({'recipient': data});

      if (data.recipient.length) {

        var txts = data.recipient.filter(this.txtfilter);
        var edms = data.recipient.filter(this.edmfilter);

        if (txts.length) {
          this.setState({'recipientTxtUrlsafe': txts[0].urlsafe});
        }

        if (edms.length) {
          this.setState({'recipientEdmUrlsafe': edms[0].urlsafe});
        }
      }

    }.bind(this));
  },

  componentWillMount: function () {
    this.addSpinners(['spinner']);
  },

  componentDidMount: function () {
    this.fetchRecipient();

    $('#datetimepicker2').datetimepicker({
      minuteStepping: 60,
      format: 'YYYY/MM/DD HH:mm',
      use24hours: true,
      defaultDate: moment().add(7, 'days')
    }).on("dp.change", function (e) {
      this.setState({'startTime': moment(e.date).format('YYYY/MM/DD HH:mm')});
    }.bind(this));
  },

  render: function () {

    var txtOptions = [], edmOptions = [];

    if (this.state.recipient.recipient) {

      var txts = this.state.recipient.recipient.filter(this.txtfilter);
      var edms = this.state.recipient.recipient.filter(this.edmfilter);

      if (txts.length) {
        for (var i = 0, j = txts.length; i < j; i++) {
          var r = txts[i];
          txtOptions.push(<option value={r.urlsafe}>{r.display_name}</option>);
        }
      }

      if (edms.length) {
        for (var l = 0, m = edms.length; l < m; l++) {
          var k = edms[l];
          edmOptions.push(<option value={k.urlsafe}>{k.display_name}</option>);
        }
      }

    }

    return (
      <div>
        <h3>{this.props.header}</h3>
        <Spinner loaded={this.getSpinner('spinner')} message="" spinWait={0} msgWait={0}>
          <p></p>
        </Spinner>
        <form className="form-horizontal">
          <div className="form-group">
            <label for="inputEmail3" className="col-sm-2 control-label">Subject</label>
            <div className="col-sm-10">
              <input type="text" className="form-control" id="subject" ref="subject" placeholder="subject" onChange={this._onChange} value={this.state.subject} required/>
            </div>
          </div>
          <div className="form-group">
            <label for="inputEmail3" className="col-sm-2 control-label">Sender Name</label>
            <div className="col-sm-10">
              <input type="text" className="form-control" id="senderName" ref="senderName" placeholder="senderName" onChange={this._onChange} value={this.state.senderName} required/>
            </div>
          </div>
          <div className="form-group">
            <label for="inputEmail3" className="col-sm-2 control-label">Sender Email</label>
            <div className="col-sm-10">
              <input type="text" className="form-control" id="senderEmail" ref="senderEmail" placeholder="senderEmail" onChange={this._onChange} value={this.state.senderEmail} required/>
            </div>
          </div>
          <div className="form-group">
            <label for="inputEmail3" className="col-sm-2 control-label">Category</label>
            <div className="col-sm-10">
              <input type="text" className="form-control" id="category" ref="category" placeholder="Category" onChange={this._onChange} value={this.state.category} required/>
            </div>
          </div>
          <div className="form-group">
            <label for="inputPassword3" className="col-sm-2 control-label">Schedule Duration</label>
            <div className="col-sm-10">
              <input type="number" className="form-control" id="scheduleDuration" ref="scheduleDuration" placeholder="scheduleDuration" onChange={this._onChange} value={this.state.scheduleDuration} required/>
            </div>
          </div>
          <div className="form-group">
            <label for="inputPassword3" className="col-sm-2 control-label">ip Counts</label>
            <div className="col-sm-10">
              <input type="number" className="form-control" id="ipCounts" ref="ipCounts" placeholder="ipCounts" onChange={this._onChange} value={this.state.ipCounts} required/>
            </div>
          </div>
          <div className="form-group">
            <label for="inputSchedule" className="col-sm-2 control-label">Job Start Time</label>

            <div className="col-sm-10">
              <div className='input-group date' id='datetimepicker2'>
                <input name="sendmail_schedule" type='text' className="form-control"
                  pattern="^(19|20)\d{2}\/(0[1-9]|1[0-2])\/(0[1-9]|1\d|2\d|3[01]) ([01]\d|2[0-3]):?[0-5]\d$"
                  required id="startTime" ref="startTime"/>
                <span className="input-group-addon">
                  <span className="glyphicon glyphicon-calendar"></span>
                </span>
              </div>
            </div>
          </div>
          <div className="form-group">
            <label for="inputPassword3" className="col-sm-2 control-label">預計執行小時(max:24)</label>
            <div className="col-sm-10">
              <input type="number" className="form-control" id="hourRate" ref="hourRate" placeholder="hourRate" onChange={this._onChange} value={this.state.hourRate} required/>
            </div>
          </div>
          <div className="form-group">
            <label for="inputSchedule" className="col-sm-2 control-label">Recipients</label>
            <div className="col-sm-10">
              <select className="form-control" id="recipientTxtUrlsafe" ref="recipientTxtUrlsafe" onChange={this._onChange}>
            {txtOptions}
              </select>
            </div>
          </div>
          <div className="form-group">
            <label for="inputSchedule" className="col-sm-2 control-label">Edm</label>
            <div className="col-sm-10">
              <select className="form-control" id="recipientEdmUrlsafe" ref="recipientEdmUrlsafe" onChange={this._onChange}>
            {edmOptions}
              </select>
            </div>
          </div>
          <div className="form-group">
            <label for="inputPassword3" className="col-sm-2 control-label">Skip</label>
            <div className="col-sm-10">
              <input type="number" className="form-control" id="recipientSkip" ref="recipientSkip" placeholder="recipientSkip" onChange={this._onChange} value={this.state.recipientSkip} required/>
            </div>
          </div>
          <div className="form-group">
            <div className="col-sm-offset-2 col-sm-10">
              <button type="submit" className="btn btn-primary" onChange={this._onChange} onClick={this._onClick}>Add</button>
            </div>
          </div>
        </form>
      </div>
    );
  },

  _onClick: function (evt) {
    evt.stopPropagation();
    evt.preventDefault();

    this.startSpinner('spinner');
    $.post('/api/ipwarmup/addjob', this.state, function (result) {
      console.log(result);
      this.stopSpinner('spinner');
      window.location.href = '/ipwarmup';
    }.bind(this));
  },

  _onChange: function (e) {
    switch (e.target.id) {
      case "category":
        this.setState({'category': e.target.value});
        break;
      case "subject":
        this.setState({'subject': e.target.value});
        break;
      case "senderName":
        this.setState({'senderName': e.target.value});
        break;
      case "senderEmail":
        this.setState({'senderEmail': e.target.value});
        break;
      case "recipientTxtUrlsafe":
        this.setState({'recipientTxtUrlsafe': e.target.value});
        break;
      case "recipientEdmUrlsafe":
        this.setState({'recipientEdmUrlsafe': e.target.value});
        break;
      case "scheduleDuration":
        this.setState({'scheduleDuration': e.target.value});
        break;
      case "ipCounts":
        this.setState({'ipCounts': e.target.value});
        break;
      case "startTime":
        this.setState({'startTime': e.target.value});
        break;
      case "recipientSkip":
        this.setState({'recipientSkip': e.target.value});
        break;
      case "hourRate":
        this.setState({'hourRate': e.target.value});
        break;
    }
  }
});

module.exports = addIPWarmupScheduleApp;