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
require('bootstrap');
var api = require('./api');


var ResourceList = React.createClass({
  render: function () {
    var items = [];

    items.push(<li>
      recipients: <code>{this.props.job.txt_object_name}</code>
    </li>);
    items.push(<li>
      edm: <code>{this.props.job.edm_object_name}</code>
    </li>);

    if (this.props.job.replace_edm_csv_property) {
      items.push(<li>
        replace properties: <code>{this.props.job.replace_edm_csv_property}</code>
      </li>);
    }

    return (
      <ul className="list-unstyled">
        {items}
      </ul>
    );
  }
});

var TasksList = React.createClass({
  render: function () {
    var unsendRecipientDownloadLink = null, sendRecipientDownloadLink = null;

    if (parseInt(this.props.detail.fail_worker, 10) > 0) {
      if (this.props.detail.unsend_recipients_log) {
        if (this.props.detail.unsend_recipients_log === 'preparing') {
          unsendRecipientDownloadLink = this.props.detail.unsend_recipients_log;
        } else {
          unsendRecipientDownloadLink = <div>
            <button type="button" className="btn btn-primary btn-xs"
                    onClick={this.props.dump.bind(this, this.props.detail.urlsafe, 'unsend')}>
              Dump unsend recipients
            </button>
            &nbsp;<a target="_blank" href={this.props.detail.unsend_recipients_log}>download</a></div>;
        }
      }
    }

    if (parseInt(this.props.detail.tasks_executed_count, 10) > 0) {
      var x = <button type="button" className="btn btn-primary btn-xs"
                      onClick={this.props.dump.bind(this, this.props.detail.urlsafe, 'send')}>Dump
        send recipients
      </button>;
      if (this.props.detail.send_recipients_log) {
        if (this.props.detail.send_recipients_log === 'preparing') {
          sendRecipientDownloadLink = <div>{x}&nbsp;{this.props.detail.send_recipients_log}</div>;
        } else {
          sendRecipientDownloadLink =
            <div>{x}&nbsp;<a target="_blank" href={this.props.detail.send_recipients_log}>download</a></div>;
        }
      } else {
        sendRecipientDownloadLink = x;
      }
    }

    return (
      <table className="table">
        <thead>
        <tr>
          <th></th>
          <th>tasks</th>
          <th></th>
        </tr>
        </thead>
        <tbody>
        <tr>
          <td>dispatch success</td>
          <td>{this.props.detail.success_worker}</td>
          <td></td>
        </tr>
        <tr>
          <td>dispatch fail</td>
          <td>{this.props.detail.fail_worker}</td>
          <td>
            {unsendRecipientDownloadLink}
          </td>
        </tr>
        <tr>
          <td>executed</td>
          <td>{this.props.detail.tasks_executed_count}</td>
          <td>
            {sendRecipientDownloadLink}
          </td>
        </tr>
        </tbody>
      </table>
    );
  }
});

var ScheduleDetail = React.createClass({
  render: function () {
    var error = null;
    if (this.props.detail.error) {
      error = <div className="form-group">
        <label className="col-sm-2 control-label">error</label>

        <div className="col-sm-10">
          <p className="form-control-static text-danger">{this.props.detail.error}</p>
        </div>
      </div>;
    }

    var taskslist, resourcelist;
    if (this.props.detail.urlsafe) {
      taskslist =
        <TasksList detail={this.props.detail} dump={this.props.dump}/>;
      resourcelist = <ResourceList job={this.props.detail}/>;
    }

    return (
      <form className="form-horizontal">
        {error}
        <div className="form-group">
          <label className="col-sm-2 control-label">Schedule</label>

          <div className="col-sm-10">
            <p className="form-control-static">{this.props.detail.error ? '' : this.props.detail.schedule_display}</p>
          </div>
        </div>
        <div className="form-group">
          <label className="col-sm-2 control-label">status</label>

          <div className="col-sm-10">
            <p className="form-control-static">{this.props.detail.status}</p>
          </div>
        </div>
        <div className="form-group">
          <label className="col-sm-2 control-label">Subject</label>

          <div className="col-sm-10">
            <p className="form-control-static">{this.props.detail.subject}</p>
          </div>
        </div>
        <div className="form-group">
          <label className="col-sm-2 control-label">Category</label>

          <div className="col-sm-10">
            <p className="form-control-static"><span className="label label-default">{this.props.detail.category}</span>
            </p>
          </div>
        </div>
        <div className="form-group">
          <label className="col-sm-2 control-label">Account</label>

          <div className="col-sm-10">
            <p className="form-control-static"><span
              className="label label-primary">{this.props.detail.sendgrid_account}</span></p>
          </div>
        </div>
        <div className="form-group">
          <label className="col-sm-2 control-label">Sender Name</label>

          <div className="col-sm-10">
            <p className="form-control-static">{this.props.detail.sender_name}</p>
          </div>
        </div>
        <div className="form-group">
          <label className="col-sm-2 control-label">Sender Email</label>

          <div className="col-sm-10">
            <p className="form-control-static">{this.props.detail.sender_email}</p>
          </div>
        </div>
        <div className="form-group">
          <label className="col-sm-2 control-label">Delta</label>

          <div className="col-sm-10">
            <p className="form-control-static">{this.props.detail.hour_delta}</p>
          </div>
        </div>
        <div className="form-group">
          <label className="col-sm-2 control-label">Capacity</label>

          <div className="col-sm-10">
            <p className="form-control-static">{this.props.detail.hour_capacity}</p>
          </div>
        </div>
        <div className="form-group">
          <label className="col-sm-2 control-label">Invalid</label>

          <div className="col-sm-10">
            <p className="form-control-static">{this.props.detail.invalid_email}</p>
          </div>
        </div>
        <div className="form-group">
          <label className="col-sm-2 control-label">Rate</label>

          <div className="col-sm-10">
            <p className="form-control-static">{this.props.detail.hour_rate}</p>
          </div>
        </div>
        <div className="form-group">
          <label className="col-sm-2 control-label">Recipient/edm</label>

          <div className="col-sm-10">
            {resourcelist}
          </div>
        </div>
        <div className="form-group">
          <label className="col-sm-2 control-label">Tasks</label>

          <div className="col-sm-10">
            {taskslist}
          </div>
        </div>
      </form>
    );
  }
});

var detailScheduleApp = React.createClass({

  mixins: [
    // Load the spinner mixin.
    // http://facebook.github.io/react/docs/reusable-components.html#mixins
    Spinner.Mixin
  ],

  getInitialState: function () {
    return {
      schedule: {},
      recipicentQueueDataHealth: []
    };
  },

  fetchSchedule: function (id) {
    this.startSpinner('spinner');

    api.getSchedule(id).done(function (result) {
      this.stopSpinner('spinner');
      this.setState({
        schedule: result
      });
    }.bind(this));
  },


  componentWillMount: function () {
    this.addSpinners(['spinner', 'fetch']);
  },

  componentDidMount: function () {
    this.fetchSchedule(this.props.id);
  },

  render: function () {
    return (
      <div>
        <Spinner loaded={this.getSpinner('spinner')} message="" spinWait={0} msgWait={0}>
          <h1 className="spinner-h1"></h1>
        </Spinner>
        <ScheduleDetail detail={this.state.schedule} healths={this.state.recipicentQueueDataHealth} dump={this.dump}/>
      </div>
    );
  },

  dump: function (id, type) {
    this.startSpinner('fetch');

    api.dumpSchedule(id, JSON.stringify({'dumpType': type})).done(function (result) {
      this.stopSpinner('fetch');
      this.setState({
        schedule: result
      });
    }.bind(this));
  }

});

module.exports = detailScheduleApp;