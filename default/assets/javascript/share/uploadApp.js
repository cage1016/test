/** @jsx React.DOM */

/*jshint browser: true */
/*jslint node: true */
/*jshint -W109*/
/*jshint -W108*/

'use strict';

var React = require('react');
var $ = require('jquery');
var MediaUploader = require('./upload');
var Spinner = require('./vitullo-spinner.jsx');
var api = require('./api');

var RecipientList = React.createClass({

  render: function () {
    var resources = [];

    if (this.props.resources) {
      for (var i = 0, j = this.props.resources.length; i < j; i++) {
        var r = this.props.resources[i];

        resources.push(
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
        {resources}
        </tbody>
      </table>
    );
  }
});


var Progress = React.createClass({
  getInitialState: function () {
    return {
      progress: 0,
      complete: true
    };
  },

  componentWillReceiveProps: function (nextProps) {

    if (nextProps.progress > this.props.progress) {
      this.setState({'progress': nextProps.progress});
    }
    if (nextProps.progress === 0) {
      this.setState({'progress': 0});
    }

    if (nextProps.complete === true) {
      var self = this;
      setTimeout(
        function () {
          self.setState({'complete': nextProps.complete});
        },
        3500
      );
    } else {
      this.setState({'complete': nextProps.complete});
    }
  },


  render: function () {
    var progressStyle = {
      'visibility': this.state.complete ? 'hidden' : 'visible'
    };
    var progressBarStyle = {
      width: this.state.progress + "%"
    };

    return (
      <div className="progress" style={progressStyle} ref="progress">
        <div className="progress-bar" role="progressbar" aria-valuenow={this.state.progress.toFixed(2)} aria-valuemin="0" aria-valuemax="100" style={progressBarStyle}>
            {this.state.progress.toFixed(2)}%
        </div>
      </div>
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
      complete: true,
      baseUrl: 'https://www.googleapis.com/upload/storage/v1/b/' + this.props.bucketName + '/o',
      resources: []
    };
  },

  fetchResource: function () {
    this.startSpinner('spinner');
    api.getResourceList().done(function (result) {
      this.stopSpinner('spinner');
      this.setState({'resources': result.data || []});
    }.bind(this));
  },

  insertResource: function (data) {
    this.startSpinner('spinner');
    api.inertResource(data).done(function (resource) {
      this.stopSpinner('spinner');

      var o = [resource].concat(this.state.resources);
      this.setState({'resources': o});

    }.bind(this));
  },

  deleteResource: function (id) {
    this.startSpinner('spinner');
    api.deleteResource(id).done(function (result) {
      this.stopSpinner('spinner');

      var o = this.state.resources;
      var index = o.map(function (x) {
        return x.urlsafe;
      }).indexOf(result.urlsafe);
      if (index > -1) {
        o.splice(index, 1);
        this.setState({'resources': o});
      }

    }.bind(this));
  },

  componentWillMount: function () {
    this.addSpinners(['spinner', 'fetch']);
  },

  componentDidMount: function () {
    this.fetchResource();

    var fileNode = this.refs.file.getDOMNode();
    fileNode.addEventListener('change', this.handleChange, false);
  },

  handleChange: function (evt) {
    this.startSpinner('spinner');
    this.setState({progress: 0});
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
        <Progress progress={this.state.progress} complete={this.state.complete}/>
        <div>
          <RecipientList resources={this.state.resources} delete={this._onDelete}/>
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
    this.setState({progress: 0});
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
    this.setState({'complete': false});
    var uploader = new MediaUploader({
      file: fileData,
      token: api.getToken(),
      params: {
        name: this.props.objectNamePerfix + '/' + api.getEmail() + '/' + fileData.name
      },
      baseUrl: this.state.baseUrl,
      onComplete: function (data) {
        this.stopSpinner('spinner');
        this.setState({'complete': true});
        this.insertResource(data);
      }.bind(this),
      onProgress: function (data) {
        var progress = (data.loaded / data.total) * 100;
        this.setState({'progress': progress});
      }.bind(this)
    });

    uploader.upload();
  },

  _onDelete: function (r) {
    this.deleteResource(r.urlsafe);
  }
});


module.exports = uploadApp;
