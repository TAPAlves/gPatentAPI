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
                        $scope.jsonData = JSON.stringify(data, null, 2);
                    })
                    .error(function (data, status, headers, config) {
                        console.log(data);
                        $scope.requestStatus = data.status;
                        $scope.jsonData = JSON.stringify(data, null, 2);
                    })
                    .then(function () {
                        console.log($scope.requestStatus);
                    });

                // Reset the form
                $scope.publicationNumber = '';
                $scope.gPatentDataForm.$setPristine();
            };
        }
    ]);
}());
