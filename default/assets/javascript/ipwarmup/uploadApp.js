/** @jsx React.DOM */

/*jshint browser: true */
/*jslint node: true */
/*jshint -W109*/
/*jshint -W108*/

'use strict';

var React = require('react');
var $ = require('jquery');
var MediaUploader = require('./upload');
var Spinner = require('../vitullo-spinner.jsx');


var RecipientList = React.createClass({

  render: function () {
    var recipients = [];

    if (this.props.recipient.recipient) {
      for (var i = 0, j = this.props.recipient.recipient.length; i < j; i++) {
        var r = this.props.recipient.recipient[i];

        recipients.push(
          <tr>
            <td>{r.display_name}</td>
            <td>{r.size}</td>
            <td>{r.content_type}</td>
            <td>{r.created}</td>
            <td>
              <button className="btn btn-xs btn-danger" onClick={this.props.delete.bind(this, r)}>Delete</button>
            </td>
          </tr>
        );
      }
    }

    return (
      <table className="table">
        <thead>
          <tr>
            <th>File Name</th>
            <th>Size</th>
            <th>Content Type</th>
            <th>Created</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
        {recipients}
        </tbody>
      </table>
    );
  }
});

var uploadApp = React.createClass({

  mixins: [
    // Load the spinner mixin.
    // http://facebook.github.io/react/docs/reusable-components.html#mixins
    Spinner.Mixin
  ],

  getInitialState: function () {
    return {
      files: [],
      response: '',
      access_token: '',
      progress: 0,
      baseUrl: 'https://www.googleapis.com/upload/storage/v1/b/cheerspoint-recipient/o',
      recipient: []
    };
  },

  fetchToken: function () {
    $.get('/api/me', function (token) {
      this.setState({'access_token': token});
    }.bind(this));
  },

  fetchRecipient: function () {
    $.get('/api/recipient', function (data) {
      this.stopSpinner('spinner');
      this.setState({'recipient': data});
    }.bind(this));
  },

  updateRecipient: function (data) {
    this.startSpinner('spinner');
    $.post('/api/recipient/insert', {data: data}, function (result) {
      console.log(result);
      this.fetchRecipient();
    }.bind(this));
  },

  componentWillMount: function () {
    this.addSpinners(['spinner', 'fetch']);
  },

  componentDidMount: function () {
    this.fetchToken();
    this.fetchRecipient();

    var fileNode = this.refs.file.getDOMNode();
    fileNode.addEventListener('change', this.handleChange, false);
  },

  handleChange: function (evt) {
    this.startSpinner('spinner');
    var files = this.refs.file.getDOMNode().files;
    for (var i = 0, j = files.length; i < j; i++) {
      //this.uploadFile(files[i]);
      this.resumableUpload(files[i]);
    }
  },

  render: function () {
    var inputStyle = {
      visibility: 'hidden',
      position: 'absolute'
    };

    return (
      <div>
        <Spinner loaded={this.getSpinner('spinner')} message="" spinWait={0} msgWait={0}>
          <h1></h1>
        </Spinner>
        <div id="drop_zone" onClick={this._onClick} onDragOver={this._onDragover} onDrop={this._onDrop}>Drop files here or click to select files.</div>
        <input style={inputStyle} type="file" ref="file"/>
        <div>{this.state.response}</div>
        <div>{this.state.progress}</div>
        <div>
          <RecipientList recipient={this.state.recipient} delete={this._onDelete}/>
        </div>
      </div>
    );
  },

  _onDragover: function (evt) {
    evt.stopPropagation();
    evt.preventDefault();
    evt.dataTransfer.dropEffect = 'copy';
  },

  _onDrop: function (evt) {
    evt.stopPropagation();
    evt.preventDefault();
    var files = evt.dataTransfer.files; // FileList object.

    this.startSpinner('spinner');
    for (var i = 0, j = files.length; i < j; i++) {
      //this.uploadFile(files[i]);
      this.resumableUpload(files[i]);
    }
  },

  _onClick: function (evt) {
    evt.stopPropagation();
    evt.preventDefault();

    this.refs.file.getDOMNode().click();
  },

  uploadFile: function (fileData) {
    var reader = new FileReader();
    reader.readAsBinaryString(fileData);
    reader.onload = function (e) {
      var contentType = fileData.type || 'application/octet-stream';
      var base64Data = btoa(reader.result);
      var that = this;
      $.post(this.props.insertUrl, {
        'body': base64Data,
        'name': fileData.name,
        'contentType': contentType
      }, function (data) {
        console.log(data);
        that.stopSpinner('spinner');
        that.setState({'response': data});
      }).fail(function (error) {
        console.log(error);
        that.stopSpinner('spinner');
        that.setState({'response': error});
      });
    }.bind(this);
  },

  resumableUpload: function (fileData) {
    var that = this;
    var uploader = new MediaUploader({
      file: fileData,
      token: this.state.access_token,
      params: {
        name: 'ipwarmup/' + fileData.name
      },
      baseUrl: this.state.baseUrl,
      onComplete: function (data) {
        console.log(data);
        that.updateRecipient(data);
        that.stopSpinner('spinner');
      },
      onProgress: function (data) {
        var progress = (data.loaded / data.total) * 100;
        that.setState({progress: progress.toFixed(2) + '%'});
      }
    });

    uploader.upload();
  },

  _onDelete: function (r) {
    $.post('/api/recipient/delete', {urlsafe: r.urlsafe}, function () {
      this.fetchRecipient();
    }.bind(this));
  }
});


module.exports = uploadApp;
