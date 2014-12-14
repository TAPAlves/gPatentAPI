(function () {
    'use strict';

    var gPatent = angular
        .module('gPatent', [
            'ui.bootstrap',
            'mgcrea.ngStrap',
            'jsonFormatter',
            'treeControl'
        ]);

    gPatent.config(['$interpolateProvider', function($interpolateProvider) {
        $interpolateProvider.startSymbol('{[');
        $interpolateProvider.endSymbol(']}');
    }]);

    gPatent.controller('PublicationController', [
        '$scope',
        '$http',
        function ($scope, $http) {
            $scope.publicationNumber = null;
            $scope.requestStatus = null;
            $scope.fullNumber = null;
            $scope.gJSONData = null;
            $scope.opsJSONData = null;
            //$scope.gPatent = null;

            $scope.get_gPatentData = function () {
                //console.log($scope.publicationNumber);

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
                        //console.log(data);
                        $scope.fullNumber = data.id;
                        $scope.requestStatus = data.status;
                        $scope.gJSONData = JSON.stringify(data, null, 2);
                        $scope.gPatent = data.claims;
                        //console.log($scope.gPatent)
                    })
                    .error(function (data, status, headers, config) {
                        //console.log(data);
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
                $scope.gPatent = '';
            };

            $scope.setTab = function (claim_elements) {
                $scope.active_element = claim_elements;
            };
        }
    ]);

    gPatent.directive("claimElement", function ($compile) {
        return {
            restrict: "E",
            transclude: true,
            scope: {element: '='},
            replace: true,
            template:
                '<div>' +
                    '<div ng-transclude></div>' +
                    '<div ng-repeat="child in element.children">' +
                        '<claim-element element="child"><div ng-transclude style="margin-left:20px;margin-top:20px;"></div></claim-element>' +
                    '</div>' +
                '</div>',
            compile: function (tElement, tAttr, transclude) {
                var contents = tElement.contents().remove(),
                    compiledContents;
                return function (scope, iElement, iAttr) {

                    if (!compiledContents) {
                        compiledContents = $compile(contents, transclude);
                    }
                    compiledContents(scope, function (clone, scope) {
                        iElement.append(clone);
                    });
                };
            }
        };
    });
}());
