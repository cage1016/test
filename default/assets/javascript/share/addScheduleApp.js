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
var api = require('./api');

var addIPWarmupScheduleApp = React.createClass({

    mixins: [
      // Load the spinner mixin.
      // http://facebook.github.io/react/docs/reusable-components.html#mixins
      Spinner.Mixin
    ],

    getInitialState: function () {
      return {
        recipient: [],
        recipientTxtUrlsafe: '',
        recipientEdmUrlsafe: '',
        category: '',
        replyTo: '',
        scheduleDuration: 1,
        ipCounts: 1,
        dailyCapacity: 1000,
        startTime: '',
        recipientSkip: 0,
        hourRate: 24,
        type: this.props.type,
        subject: '',
        senderEmail: 'mitac2hr@edm1.micloud.asia',
        senderName: 'mitac2hr',
        sendgridAccount: 'mitac2hr',
        replaceEdmCSVProperty:'' // 使用者要在 html 置換什麼 csv 的欄位
      };
    },

    txtfilter: function (r) {
      return r.content_type === 'text/csv';
    },

    edmfilter: function (r) {
      return r.content_type === 'text/html';
    },

    fetchResource: function () {
      this.startSpinner('spinner');

      api.getResourceList().done(function (result) {
        this.stopSpinner('spinner');
        var data = result.data || [];

        this.setState({'recipient': data});

        if (data.length) {

          var txts = data.filter(this.txtfilter);
          var edms = data.filter(this.edmfilter);

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
      this.fetchResource();

      $('#datetimepicker2').datetimepicker({
        minuteStepping: 60,
        format: 'YYYY/MM/DD HH:mm',
        use24hours: true,
        defaultDate: moment().add(0, 'days')
      }).on("dp.change", function (e) {
        this.setState({'startTime': moment(e.date).format('YYYY/MM/DD HH:mm')});
      }.bind(this));
    },

    render: function () {

      var txtOptions = [], edmOptions = [];

      if (this.state.recipient.length) {

        var txts = this.state.recipient.filter(this.txtfilter);
        var edms = this.state.recipient.filter(this.edmfilter);

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
              <label for="inputEmail3" className="col-sm-2 control-label">Sendgrid Account</label>
              <div className="col-sm-10">
                <select className="form-control" id="sendgridAccount" ref="sendgridAccount" onChange={this._onChange}>
                  <option value="mitac2hr">Cheerspoint:mitac-2hr</option>
                  <option value="mitacmax">Cheerspoint:mitac-max</option>
                  <option value="mitacwarmup1">Cheerspoint:mitac-warmup1</option>
                  <option value="mitacwarmup2">Cheerspoint:mitac-warmup2</option>
                  <option value="mitacsymphox">mitac-symphox (神坊主帳號)</option>
                </select>
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
              <label for="inputEmail3" className="col-sm-2 control-label">Reply To</label>
              <div className="col-sm-10">
                <input type="text" className="form-control" id="replyTo" ref="replyTo" placeholder="replyTo" onChange={this._onChange} value={this.state.replyTo} required/>
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

              <div className="row">
                <div className="col-sm-12">
                  <label for="inputPassword3" className="col-sm-2 control-label">Daily capacity</label>
                  <div className="col-sm-10">
                    <input type="number" className="form-control" id="dailyCapacity" ref="dailyCapacity" placeholder="dailyCapacity" onChange={this._onChange} value={this.state.dailyCapacity} required/>
                  </div>
                </div>
              </div>
              <div className="row">
                <div className="col-sm-12">
                  <label for="inputPassword3" className="col-sm-2 control-label"></label>
                  <div className="col-sm-10">
                    <div className="well add-schedule-capacity">
                      daily_quota = 2^(day) * Daily_capacity * ip_count
                    </div>
                  </div>
                </div>
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
              <label for="replaceEdmCSVProperty" className="col-sm-2 control-label">Replace edm with CSV property</label>
              <div className="col-sm-10">
                <input type="text" className="form-control" id="replaceEdmCSVProperty" ref="replaceEdmCSVProperty" placeholder="Replace edm with CSV Property" onChange={this._onChange} value={this.state.replaceEdmCSVProperty} required/>
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
                <button type="submit" className="btn btn-primary" onChange={this._onChange} onClick={this._onClick}>Add Job</button>
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

      api.insertSchedule(JSON.stringify({
          category: this.state.category.trim(),
          replyTo: this.state.replyTo.trim(),
          dailyCapacity: this.state.dailyCapacity,
          hourRate: this.state.hourRate,
          ipCounts: this.state.ipCounts,
          recipientEdmUrlsafe: this.state.recipientEdmUrlsafe,
          recipientTxtUrlsafe: this.state.recipientTxtUrlsafe,
          recipientSkip: this.state.recipientSkip,
          scheduleDuration: this.state.scheduleDuration,
          sendgridAccount: this.state.sendgridAccount.trim(),
          senderEmail: this.state.senderEmail.trim(),
          senderName: this.state.senderName.trim(),
          startTime: this.state.startTime,
          subject: this.state.subject.trim(),
          type: this.state.type,
          replaceEdmCSVProperty: this.state.replaceEdmCSVProperty.trim()
        })
      ).done(function (result) {
          console.log(result);
          this.stopSpinner('spinner');
          window.location.href = '/ipwarmup';
        }.bind(this)).fail(function (error) {
          console.error(error);
          this.stopSpinner('spinner');
          window.location.reload();
        }.bind(this));
    },

    _onChange: function (e) {
      switch (e.target.id) {
        case "sendgridAccount":
          this.setState({'sendgridAccount': e.target.value});

          switch (e.target.value.trim()) {
            case "mitac2hr":
              this.setState({'senderEmail': 'mitac2hr@edm1.micloud.asia'});
              this.setState({'senderName': 'mitac2hr'});
              break;
            case "mitacmax":
              this.setState({'senderEmail': 'mitacmax@edm2.micloud.asia'});
              this.setState({'senderName': 'mitacmax'});
              break;
            case "mitacwarmup1":
              this.setState({'senderEmail': 'mitacwarmup1@edm3.micloud.asia'});
              this.setState({'senderName': 'mitacwarmup1'});
              break;
            case "mitacwarmup2":
              this.setState({'senderEmail': 'mitacwarmup2@em.micloud.asia'});
              this.setState({'senderName': 'mitacwarmup2'});
              break;
            case "mitacsymphox":
              this.setState({'senderEmail': 'treemall@mda.treemall.com.tw'});
              this.setState({'senderName': 'mitacsymphox'});
              break;
          }

          break;
        case "category":
          this.setState({'category': e.target.value});
          break;
        case "replyTo":
          this.setState({'replyTo': e.target.value});
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
        case "dailyCapacity":
          this.setState({'dailyCapacity': e.target.value});
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
        case "replaceEdmCSVProperty":
          this.setState({'replaceEdmCSVProperty': e.target.value});
          break;
      }
    }
  })
  ;

module.exports = addIPWarmupScheduleApp;