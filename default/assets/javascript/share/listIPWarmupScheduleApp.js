/** @jsx React.DOM */

/*jshint browser: true */
/*jslint node: true */
/*jshint -W109*/
/*jshint -W108*/

'use strict';

var React = require('react');
var $ = require('jquery');
var Spinner = require('./vitullo-spinner.jsx');
var api = require('./api');

var LoadMore = React.createClass({

  render: function () {

    var rowStyle = {
      'display': 'none'
    };

    if (this.props.next_cursor) {
      rowStyle.display = 'block';
    }

    return (
      <div className="row" style={rowStyle}>
        <div className="col-sm-12 col-md-12">
          <div className="btn-group" role="group" aria-label="...">
            <div className="btn-group" role="group">
              <button type="button" className="btn btn-default" onClick={this._onClick}>{this.props.status}</button>
            </div>
          </div>
        </div>
      </div>
    );
  },

  _onClick: function () {
    this.props.loadMore();
  }
});

var Filter = React.createClass({
  getInitialState: function () {
    return {
      categories: ''
    };
  },

  render: function () {
    return (
      <div className="well well-sm" onSubmit={this._onChange}>
        <form className="form-inline">
          <div className="form-group">
            <label for="exampleInputName2">Category</label>
            <input type="text" className="form-control" id="exampleInputName2" placeholder="Type Category" onChange={this._onChange} value={this.state.categories}/>
          </div>
          <button type="submit" className="btn btn-primary" onClick={this._onClick}>Search</button>
        </form>
      </div>
    );
  },

  _onChange: function (evt) {
    this.setState({'categories': evt.target.value});
  },

  _onClick: function(evt){
    evt.stopPropagation();
    evt.preventDefault();

    this.props.filter(this.state.categories);
  }
});

var listIPWarmupScheduleApp = React.createClass({

  mixins: [
    // Load the spinner mixin.
    // http://facebook.github.io/react/docs/reusable-components.html#mixins
    Spinner.Mixin
  ],

  getInitialState: function () {
    return {
      jobs: [],
      next_cursor: '',
      pre_cursor: '',
      status: 'Load More',
      categories: '' // category filter,
    };
  },

  fetchSchedule: function (parameters) {
    this.parameters = parameters || {};
    this.startSpinner('spinner');

    api.getScheduleList(parameters).done(function (result) {
      this.stopSpinner('spinner');

      this.setState({
        jobs: (this.parameters.loadmore) ? this.state.jobs.concat(result.data || []) : result.data,
        next_cursor: result.next_cursor,
        pre_cursor: result.pre_cursor
      });

    }.bind(this));
  },

  deleteSchedule: function (id) {
    this.startSpinner('spinner');
    api.deleteSchedule(id).done(function (result) {
      this.stopSpinner('spinner');

      var o = this.state.jobs;
      var index = o.map(function (x) {
        return x.urlsafe;
      }).indexOf(result.urlsafe);
      if (index > -1) {
        o.splice(index, 1);
        this.setState({'jobs': o});
      }

    }.bind(this));
  },


  componentWillMount: function () {
    this.addSpinners(['spinner', 'fetch']);
  },

  componentDidMount: function () {
    this.fetchSchedule();
  },

  render: function () {
    var jobs = [];

    if (this.state.jobs) {

      for (var i = 0, j = this.state.jobs.length; i < j; i++) {
        var job = this.state.jobs[i];
        jobs.push(
          <tr>
            <td>{job.schedule_executed ? 'Yes' : ''}</td>
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
              <button className="btn btn-xs btn-danger" onClick={this._onClick.bind(this, job)}>Delete</button>
            </td>
          </tr>
        );
      }

    }

    return (
      <div>
        <Spinner loaded={this.getSpinner('spinner')} message="" spinWait={0} msgWait={0}>
          <h1 className="spinner-h1"></h1>
        </Spinner>
        <Filter filter={this.triggerFilter}/>
        <table className="table">
          <thead>
            <tr>
              <th>executed</th>
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
        <LoadMore next_cursor={this.state.next_cursor} loadMore={this.loadMore} status={this.state.status}/>
      </div>
    );
  },

  _onClick: function (job) {
    this.deleteSchedule(job.urlsafe);
  },

  loadMore: function () {
    this.fetchSchedule({c: this.state.next_cursor, 'categories': this.state.categories, 'loadmore': true});
  },

  triggerFilter: function (categories) {
    this.setState({'categories': categories});
    this.fetchSchedule({'categories': categories, 'loadmore': false});
  }

});

module.exports = listIPWarmupScheduleApp;