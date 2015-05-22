/** @jsx React.DOM */

/*jshint browser: true */
/*jslint node: true */
/*jshint -W109*/
/*jshint -W108*/

'use strict';

var React = require('react');
var $ = require('jquery');
var Spinner = require('./vitullo-spinner.jsx');

var listIPWarmupScheduleApp = React.createClass({

  mixins: [
    // Load the spinner mixin.
    // http://facebook.github.io/react/docs/reusable-components.html#mixins
    Spinner.Mixin
  ],

  getInitialState: function () {
    return {
      jobs: {}
    };
  },

  fetchRecipient: function () {
    this.startSpinner('spinner');
    $.get('/api/ipwarmup/joblist', function (data) {
      this.stopSpinner('spinner');
      this.setState({'jobs': data});
    }.bind(this));
  },

  componentWillMount: function () {
    this.addSpinners(['spinner', 'fetch']);
  },

  componentDidMount: function () {
    this.fetchRecipient();
  },

  render: function () {
    var jobs = [];

    if (this.state.jobs) {

      for (var i = 0, j = this.state.jobs.length; i < j; i++) {
        var job = this.state.jobs[i];
        jobs.push(
          <tr>
            <td>{job.subject}</td>
            <td>{job.category}</td>
            <td>{job.schedule_display}</td>
            <td>{job.hour_delta}</td>
            <td>{job.hour_capacity}</td>
            <td>{job.hour_rate}</td>
            <td>
              <ul className="list-unstyled">
                <li>{job.txt_object_name}</li>
                <li>{job.edm_object_name}</li>
              </ul>
            </td>
            <td>{job.created}</td>
            <td>

            </td>
          </tr>
        );
      }

    }

    return (
      <table className="table">
        <thead>
          <tr>
            <th>subject</th>
            <th>Category</th>
            <th>Schedule</th>
            <th>Delta</th>
            <th>Capacity</th>
            <th>Rate</th>
            <th>Recipient</th>
            <th>Created</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
        {jobs}
        </tbody>
      </table>
    );
  },

  _onClick: function (evt) {
    evt.stopPropagation();
    evt.preventDefault();


  }

});

module.exports = listIPWarmupScheduleApp;