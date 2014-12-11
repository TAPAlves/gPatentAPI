(function () {
    'use strict';

    var gPatent = angular
        .module('gPatent', [
            'jsonFormatter'
        ]);


    gPatent.controller('PublicationController', [
        '$scope',
        '$http',
        function ($scope, $http) {
            $scope.publicationNumber = null;
            $scope.requestStatus = null;
            $scope.fullNumber = null;

            $scope.get_gPatentData = function () {
                console.log($scope.publicationNumber);

                // Get the Google Patent Data
                $http({
                    method: 'POST',
                    url: '/patent',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    data: JSON.stringify($scope.publicationNumber)
                })
                    .success(function (data, status, headers, config) {
                        console.log(data);
                        $scope.fullNumber = data.id;
                        $scope.requestStatus = data.status;
                        $scope.gJSONData = JSON.stringify(data, null, 2);
                    })
                    .error(function (data, status, headers, config) {
                        console.log(data);
                        $scope.requestStatus = data.status;
                        $scope.gJSONData = JSON.stringify(data, null, 2);
                    });

                // Get the OPS data
                $http.jsonp('http://ops.epo.org/3.1/rest-services/published-data/publication/epodoc/' + $scope.publicationNumber + '/biblio.js?callback=JSON_CALLBACK')
                    .success(function (data, status, headers, config) {
                        //console.log(data);
                        $scope.opsJSONData = JSON.stringify(data, null, 2);
                    })
                    .error(function (data, status, headers, config) {
                        $scope.opsJSONData = JSON.stringify({'status': 404, 'message': 'Not found - ' + $scope.publicationNumber});
                    });
            };

            $scope.resetgPatentDataForm = function () {

                // Reset the form
                $scope.clearJSON();
                $scope.publicationNumber = '';
                $scope.gPatentDataForm.$setPristine();

            };

            $scope.clearJSON = function () {
                $scope.gJSONData = '';
                $scope.opsJSONData = '';
            };
        }
    ]);
}());
