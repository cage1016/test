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

CheeerspointAPI.prototype.getResourceList = function () {
  function run(apiRoot, token) {
    return $.ajax({
      url: apiRoot + '/cheerspoint/v1/resources',
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


module.exports = new CheeerspointAPI();