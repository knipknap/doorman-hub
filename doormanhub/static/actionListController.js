app.controller('actionListController', function($scope) {
    $scope.actions = [
        {name:'Jani',description:'Norway'},
        {name:'Hege',description:'Sweden'},
        {name:'Kai',description:'Denmark'}
    ];

    /*
    $scope.action_clicked = function(id) {
        hub.call('action/1.0/action/start',
                      {'id': action.id},
                      function(data) { //success
                          $scope.error = 'success!';
                      },
                      function(response) { //error
                          $scope.error = response.statusText;
                      });
    };

    hub.call('action/1.0/action/list',
                  {'limit': 1000, 'offset': 0},
                  function(data) {
                      console.log(data);
                      $scope.actions = data.list;
                  },
                  function(response) { //error
                      $scope.error = response.statusText;
                  });
    */
});
