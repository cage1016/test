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
      categories: '',
      showDeleting: false
    };
  },

  render: function () {
    return (
      <div className="controller-panel">
        <form className="form-inline" onSubmit={this._onChange}>
          <div className="form-group">
            <label for="exampleInputName2">Category</label>
            <input type="text" className="form-control" id="exampleInputName2" placeholder="Type Category"
                   onChange={this._onChange} value={this.state.categories}/>
          </div>
          <button type="submit" className="btn btn-primary" onClick={this._onClick}>Search</button>
          <div className="checkbox form-group">
            <label>
              <input type="checkbox" onClick={this._onShowDeletingClick} checked={this.state.showDeleting}/> Show
              Deleting ({this.props.num_deleting})
            </label>
          </div>
          <button type="button" className="btn btn-default">
            <span className="glyphicon glyphicon-play"></span></button>
          <button type="button" className="btn btn-default" onClick={this._onFefreshClick}><span
            className="glyphicon glyphicon-repeat"></span>
          </button>
        </form>
      </div>
    );
  },

  _onChange: function (evt) {
    this.setState({'categories': evt.target.value});
  },

  _onClick: function (evt) {
    evt.stopPropagation();
    evt.preventDefault();

    this.props.filter(this.state.categories);
  },

  _onFefreshClick: function (evt) {
    evt.stopPropagation();
    evt.preventDefault();

    this.props.refresh();
  },

  _onShowDeletingClick: function (evt) {
    this.props.showDeleting(!this.state.showDeleting);
    this.setState({'showDeleting': !this.state.showDeleting});
  }
});

var ResourceList = React.createClass({
  render: function () {
    var items = [];

    items.push(<li>
      <code>{this.props.job.txt_object_name}</code>
    </li>);
    items.push(<li>
      <code>{this.props.job.edm_object_name}</code>
    </li>);

    if (this.props.job.replace_edm_csv_property) {
      items.push(<li>
        <code>{this.props.job.replace_edm_csv_property}</code>
      </li>);
    }

    return (
      <ul className="list-unstyled">
        {items}
      </ul>
    );
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
      categories: '', // category filter,
      showDeleting: false
    };
  },

  fetchSchedule: function (parameters) {
    this.parameters = parameters || {};
    this.startSpinner('spinner');

    api.getScheduleList(parameters).done(function (result) {
      this.stopSpinner('spinner');

      this.setState({
        jobs: (this.parameters.loadmore) ? this.state.jobs.concat(result.data || []) : result.data || [],
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
        o.splice(index, 1, result);
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

  showFilter: function () {
    if (this.state.showDeleting) {
      return this.state.jobs;
    } else {
      return this.state.jobs.filter(function (job) {
        return job.status != 'deleting';
      });
    }
  },

  getDeletingCount: function () {
    return this.state.jobs.filter(function (job) {
      return job.status === 'deleting';
    }).length;
  },

  render: function () {
    var jobs = [];
    var num_deleting = this.getDeletingCount();
    var _d = this.showFilter();
    for (var i = 0, j = _d.length; i < j; i++) {
      var job = _d[i];
      var sign = null, sign2 = null, sign3=null, capacity = null, dry=null;
      if (job.error) {
        sign2 = <span className="glyphicon glyphicon-thumbs-down"></span>;
      }
      if (parseInt(job.fail_worker, 10) > 0) {
        sign = <span className="glyphicon glyphicon-exclamation-sign"></span>;
      }
      if (job.unsend_recipients_log === 'preparing' || job.send_recipients_log === 'preparing'){
        sign3 = <span className="glyphicon glyphicon-transfer"></span>;
      }

      if (job.status === 'parsing') {
        capacity = job.hour_capacity + '/' + job.hour_target_capacity;
      } else {
        capacity = job.hour_capacity;
      }

      jobs.push(
        <tr>
          <td>{sign} {sign2} {sign3}</td>
          <td>{job.error ? '' : job.schedule_display}</td>
          <td>{job.status}</td>
          <td>
            <ul className="list-unstyled">
              <li><span className="label label-primary">{job.sendgrid_account}</span></li>
              <li>{job.sender_name}</li>
              <li>{job.sender_email}</li>
            </ul>
          </td>
          <td>
            <div>
              <a href={'/ipwarmup/detail/' + job.urlsafe}>{job.subject}</a>
            </div>
            <span className="label label-default">{job.category}</span>
            <span className="label label-warning">{job.is_dry_run ? 'dry run':''}</span>
          </td>
          <td>{job.hour_delta}</td>
          <td>{capacity}</td>
          <td>{job.invalid_email}</td>
          <td>{job.hour_rate}</td>
          <td>
            <ResourceList job={job}/>
          </td>
          <td>{job.created}</td>
          <td>
            <button className="btn btn-xs btn-danger" onClick={this._onClick.bind(this, job)}>Delete</button>
          </td>
        </tr>
      );
    }

    return (
      <div>
        <Spinner loaded={this.getSpinner('spinner')} message="" spinWait={0} msgWait={0}>
          <h1 className="spinner-h1"></h1>
        </Spinner>
        <Filter filter={this.triggerFilter} refresh={this.triggerRefresh} num_deleting={num_deleting}
                showDeleting={this.showDeleting}/>
        <table className="table">
          <thead>
          <tr>
            <th></th>
            <th>Schedule</th>
            <th>status</th>
            <th>account/sender</th>
            <th>subject</th>
            <th>Delta</th>
            <th>Capacity</th>
            <th>Invalid</th>
            <th>Rate</th>
            <th>Recipient/edm</th>
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
  },

  triggerRefresh: function () {
    this.fetchSchedule();
  },

  showDeleting: function (show) {
    this.setState({'showDeleting': show});
  }

});

module.exports = listIPWarmupScheduleApp;