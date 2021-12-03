var DoormanHub = function(api_url) {
    this._mkurl = function(action, params) {
        var url = api_url + '/' + action;
        if (typeof params === 'undefined')
            return url;
        return url + "?" + $.param(params);
    };

    this.get = function(action, params, on_success, on_error) {
        var url = this._mkurl(action, params);
        $.getJSON(url, function(data, status) {
            if (status !== "success") {
                on_error(data.status, JSON.stringify(data));
                return;
            }
            if (typeof(data) === 'undefined' || isNaN(data.status)) {
                on_error(null, JSON.stringify(data));
                return;
            }
            if (Math.floor(data.status / 100) == 2)
                on_success(data);
            else
                on_error(data.status, data.msg);
        });
    };
    
    this.post = function(action, get_params, post_params, on_success, on_error) {
        post_params = post_params ? post_params : {};
        var url = this._mkurl(action, get_params);
        var post_data = JSON.stringify(post_params);
        $.ajax({
            'url': url,
            'type': 'post',
            'dataType': 'json',
            'contentType': 'application/json; charset=utf-8',
            'data': post_data}).done(function(data, status){
            if (status !== "success") {
                on_error(data.status, data.msg);
                return;
            }
            if (typeof(data) === 'undefined') {
                on_error(null, 'empty response from server');
                return;
            }
            on_success(data);
        }).error(function(data) {
            if (data.responseJSON === undefined)
                on_error(data.status, JSON.stringify(data));
            else
                on_error(data.status, data.responseJSON.msg);
        });
    };

    this.call = function(api, params, on_success, on_error) {
        this.post(api, undefined, params, on_success, on_error);
    };

    this.login = function(email, password, expires, on_success, on_error) {
        var post_params = {'password': password, 'email': email};
        this.call('auth/1.0/session/start',
                  post_params,
                  function(data) {
                      Cookies.set("sid", data.sid, {expires: expires});
                      on_success(data.email);
                  },
                  function(status, msg) {
                      if (status == 401)
                          on_error(401, 'Login failed. Please try again.');
                      else
                          on_error(status, msg);
                  });
    };

    this.logout = function(on_success, on_error) {
        this.call('auth/1.0/session/end',
                  undefined,
                  function(data) {
                      Cookies.remove("sid");
                      on_success(data.email);
                  },
                  on_error);
    };

    this.check_session = function(on_success, on_error) {
        var sid = Cookies.get("sid");
        if (sid === undefined)
            return;
        this.call('auth/1.0/session/check',
                  undefined,
                  function(data) {
                      if (!data.sid)
                          Cookies.remove("sid");
                      if (on_success)
                          on_success(data.sid);
                  },
                  function(status, msg) {
                      if (on_error)
                          on_error(status, msg);
                  });
    };

    this.is_logged_in = function() {
        return typeof(Cookies.get("sid")) !== 'undefined'
    };

    this.define_admin = function(email, password, on_success, on_error) {
        var post_params = {'password': password, 'email': email};
        this.call('auth/1.0/user/define_admin',
                  post_params,
                  function(data) {
                      on_success(data.email);
                  },
                  on_error);
    };

    this.check_session();
};
