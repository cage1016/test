var CheeerspointAPI = function () {
  this.apiRoot = '/_ah/api';
};

CheeerspointAPI.prototype.getToken = function () {
  return this.token;
};

CheeerspointAPI.prototype.getEmail = function () {
  return this.email;
};

CheeerspointAPI.prototype.fetchToken = function () {
  return $.ajax({
    method: 'POST',
    url: '/me'
  }).then(function (data) {
    this.token = data.token;
    this.email = data.email;
  }.bind(this));
};

CheeerspointAPI.prototype.getResourceList = function (parameters) {
  function run(apiRoot, token) {
    return $.ajax({
      url: apiRoot + '/cheerspoint/v1/resources' + ((parameters) ? '?' + $.param(parameters) : ''),
      beforeSend: function (xhr) {
        xhr.setRequestHeader("Authorization", "Bearer " + token);
      }.bind(this)
    });
  }

  if (this.token) {
    return run(this.apiRoot, this.token);
  } else {
    return this.fetchToken().then(function () {
      return run(this.apiRoot, this.token);
    }.bind(this));
  }
};

CheeerspointAPI.prototype.inertResource = function (data) {
  function run(apiRoot, token) {
    return $.ajax({
      url: apiRoot + '/cheerspoint/v1/resources',
      method: 'POST',
      data: data,
      beforeSend: function (xhr) {
        xhr.setRequestHeader("Authorization", "Bearer " + token);
        xhr.setRequestHeader("Content-Type", "application/json");
      }.bind(this)
    });
  }

  if (this.token) {
    return run(this.apiRoot, this.token);
  } else {
    return this.fetchToken().then(function () {
      return run(this.apiRoot, this.token);
    }.bind(this));
  }
};

CheeerspointAPI.prototype.deleteResource = function (id) {
  function run(apiRoot, token) {
    return $.ajax({
      url: apiRoot + '/cheerspoint/v1/resources/' + id,
      method: 'DELETE',
      beforeSend: function (xhr) {
        xhr.setRequestHeader("Authorization", "Bearer " + token);
      }.bind(this)
    });
  }

  if (this.token) {
    return run(this.apiRoot, this.token);
  } else {
    return this.fetchToken().then(function () {
      return run(this.apiRoot, this.token);
    }.bind(this));
  }
};

CheeerspointAPI.prototype.getScheduleList = function (parameters) {
  function run(apiRoot, token) {
    return $.ajax({
      url: apiRoot + '/cheerspoint/v1/schedules' + ((parameters) ? '?' + $.param(parameters) : ''),
      beforeSend: function (xhr) {
        xhr.setRequestHeader("Authorization", "Bearer " + token);
      }.bind(this)
    });
  }

  if (this.token) {
    return run(this.apiRoot, this.token);
  } else {
    return this.fetchToken().then(function () {
      return run(this.apiRoot, this.token);
    }.bind(this));
  }
};

CheeerspointAPI.prototype.getSchedule = function (id) {
  function run(apiRoot, token) {
    return $.ajax({
      url: apiRoot + '/cheerspoint/v1/schedules/' + id,
      beforeSend: function (xhr) {
        xhr.setRequestHeader("Authorization", "Bearer " + token);
      }.bind(this)
    });
  }

  if (this.token) {
    return run(this.apiRoot, this.token);
  } else {
    return this.fetchToken().then(function () {
      return run(this.apiRoot, this.token);
    }.bind(this));
  }
};

CheeerspointAPI.prototype.insertSchedule = function (data) {
  function run(apiRoot, token) {
    return $.ajax({
      url: apiRoot + '/cheerspoint/v1/schedules',
      method: 'POST',
      data: data,
      beforeSend: function (xhr) {
        xhr.setRequestHeader("Authorization", "Bearer " + token);
        xhr.setRequestHeader("Content-Type", "application/json");
      }.bind(this)
    });
  }

  if (this.token) {
    return run(this.apiRoot, this.token);
  } else {
    return this.fetchToken().then(function () {
      return run(this.apiRoot, this.token);
    }.bind(this));
  }
};

CheeerspointAPI.prototype.deleteSchedule = function (id) {
  function run(apiRoot, token) {
    return $.ajax({
      url: apiRoot + '/cheerspoint/v1/schedules/' + id,
      method: 'DELETE',
      beforeSend: function (xhr) {
        xhr.setRequestHeader("Authorization", "Bearer " + token);
      }.bind(this)
    });
  }

  if (this.token) {
    return run(this.apiRoot, this.token);
  } else {
    return this.fetchToken().then(function () {
      return run(this.apiRoot, this.token);
    }.bind(this));
  }
};

CheeerspointAPI.prototype.dumpSchedule = function (id, data) {
  function run(apiRoot, token) {
    return $.ajax({
      url: apiRoot + '/cheerspoint/v1/schedule/dump/' + id,
      method: 'POST',
      data: data,
      beforeSend: function (xhr) {
        xhr.setRequestHeader("Authorization", "Bearer " + token);
        xhr.setRequestHeader("Content-Type", "application/json");
      }.bind(this)
    });
  }

  if (this.token) {
    return run(this.apiRoot, this.token);
  } else {
    return this.fetchToken().then(function () {
      return run(this.apiRoot, this.token);
    }.bind(this));
  }
};

CheeerspointAPI.prototype.getRecipicentQueueDataHealthList = function (id) {
  function run(apiRoot, token) {
    return $.ajax({
      url: apiRoot + '/cheerspoint/v1/recipientQueueDataHealth/' + id,
      beforeSend: function (xhr) {
        xhr.setRequestHeader("Authorization", "Bearer " + token);
      }.bind(this)
    });
  }

  if (this.token) {
    return run(this.apiRoot, this.token);
  } else {
    return this.fetchToken().then(function () {
      return run(this.apiRoot, this.token);
    }.bind(this));
  }
};



module.exports = new CheeerspointAPI();