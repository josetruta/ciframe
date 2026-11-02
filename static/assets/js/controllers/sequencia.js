angular.module('deciframeApp').controller('SequenciaController', function($http, $window, ngProgressFactory, $anchorScroll, $location, GENEROS) {
  var COR_ACORDE = '#2E1C74';
  var vm = this;
  vm.sequencias = [];
  vm.carregandoSequencias = false;
  vm.erroSequencia = "";
  vm.sucessoSequencia = "";
  vm.novaSequenciaTexto = "";
  vm.minhaSequencia = {};
  vm.isSearching = false;
  vm.showSearchResultsCount = false;
  vm.esfigeSpeech =  "";
  vm.musics = [];
  vm.generos = GENEROS;
  vm.meuGenero = "";
  vm.progressbar = ngProgressFactory.createInstance();

  var mapearSequencia = function(sequencia) {
    return {
      'id': sequencia.id,
      'acordes': sequencia.acordes.map(function(acorde) {
        return { 'acorde': acorde, 'cor': COR_ACORDE };
      })
    };
  };

  var separarAcordes = function(texto) {
    if (!texto) {
      return [];
    }
    return texto.split(/[\s,]+/).filter(function(acorde) {
      return acorde.length > 0;
    });
  };

  vm.carregarSequencias = function(callback) {
    vm.carregandoSequencias = true;
    $http.get('sequencias')
      .success(function(data) {
        vm.sequencias = data.map(mapearSequencia);
        vm.carregandoSequencias = false;
        if (callback) {
          callback();
        }
      })
      .error(function() {
        vm.carregandoSequencias = false;
        vm.erroSequencia = "Não foi possível carregar o catálogo de sequências.";
      });
  };

  vm.criarSequencia = function() {
    vm.erroSequencia = "";
    vm.sucessoSequencia = "";
    var acordes = separarAcordes(vm.novaSequenciaTexto);

    if (acordes.length === 0) {
      vm.erroSequencia = "Informe pelo menos um acorde.";
      return;
    }
    if (acordes.length > 20 || acordes.some(function(acorde) { return acorde.length > 20; })) {
      vm.erroSequencia = "Use no máximo 20 acordes de até 20 caracteres.";
      return;
    }

    $http.post('sequencias', { 'acordes': acordes })
      .success(function(data) {
        vm.novaSequenciaTexto = "";
        vm.sucessoSequencia = "Sequência cadastrada.";
        vm.carregarSequencias(function() {
          var nova = vm.sequencias.filter(function(sequencia) {
            return sequencia.id === data.id;
          })[0];
          vm.pesquisarPorSequencia(nova || mapearSequencia(data));
        });
      })
      .error(function(data, status) {
        if (status === 409 && data && data.id) {
          vm.erroSequencia = "Essa sequência já existe; selecionando a existente.";
          vm.carregarSequencias(function() {
            var existente = vm.sequencias.filter(function(sequencia) {
              return sequencia.id === data.id;
            })[0];
            vm.pesquisarPorSequencia(existente || {
              'id': data.id,
              'acordes': acordes.map(function(acorde) {
                return { 'acorde': acorde, 'cor': COR_ACORDE };
              })
            });
          });
        } else {
          vm.erroSequencia = (data && data.erro) ? data.erro : "Não foi possível cadastrar a sequência.";
        }
      });
  };

  vm.temAcorde = function(acorde) {
    if (vm.minhaSequencia.acordes) {
      return (vm.minhaSequencia.acordes.indexOf(acorde) > -1);
    } else {
      return false;
    }
  }

  vm.pesquisarPorSequencia = function(sequencia) {
    if (sequencia) {
      vm.minhaSequencia = sequencia;
    }
    if (!vm.minhaSequencia || !vm.minhaSequencia.id) {
      return;
    }
    vm.progressbar.start();
    vm.esfigeSpeech = "Procurando músicas com base na sequencia...";
    vm.isSearching = true;
    vm.musics = [];

    var searchString = "similares?sequencia=" + vm.minhaSequencia.id;
    if (vm.meuGenero !== "" && vm.meuGenero !== null) {
      searchString += "&generos=" + encodeURIComponent(vm.meuGenero);
    }
    $http.get(searchString)
      .success(function(data) {
        vm.progressbar.complete();
        vm.esfigeSpeech = "Encontrei essas músicas";
        vm.isSearching = false;
        vm.showSearchResultsCount = true;
        vm.musics = data;
      })
      .error(function(data) {
        vm.esfigeSpeech = "Ops! Algo errado.";
        vm.isSearching = false;
        vm.showSearchResultsCount = false;
      });
  }

  vm.limparPesquisa = function() {
    vm.minhaSequencia = {};
    vm.musics = [];
  }

  vm.goToLirics = function(music) {
    $window.open(music.url);
  };

  vm.goToResults = function() {
    vm.showSearchResultsCount = false;
    $("body").animate({scrollTop: $("#results").offset().top}, "slow");
  };

  vm.carregarSequencias();
});
