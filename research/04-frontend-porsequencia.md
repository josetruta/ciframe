# Pesquisa 4 — O que a página `#/porsequencia` já faz

> Documento descritivo do código em `fb97001` (2026-10-17). Não contém proposta,
> avaliação ou trabalho futuro. As referências usam `caminho/arquivo.ext:linha`.

## Escopo e método

Pergunta respondida: a pergunta 4 de
`docs/features/sequencias-customizadas/01-research.md:26-32` — o que a página
`#/porsequencia` (`static/templates/sequencia.html` +
`static/assets/js/controllers/sequencia.js`) já faz, incluindo a lista hardcoded
de 4 sequências no JavaScript, diferente das 6 do backend.

Método: leitura integral de `static/index.html`, `static/assets/js/app.js`,
`static/assets/js/routes.js`, `static/assets/js/controllers/sequencia.js`,
`static/templates/sequencia.html`, `static/assets/js/directives/df-hex.js`,
`static/templates/directives/df-hex.html`, `static/assets/css/app.css` e
`static/templates/home.html`; leitura das telas irmãs `acordes.html` e
`musica.html` para contraste; leitura de `main.py:170-228` para o contrato da API;
execução da API real para confirmar os conjuntos e a paginação.

## Sumário

A página `#/porsequencia` é uma tela AngularJS 1.4.9 com dois painéis: à esquerda,
**4 cartões de sequências hardcoded no controller** (`Bm G D A`, `C G Am F`,
`Gm F`, `C C7 F Fm`); à direita, os resultados. Clicar num cartão monta
`similares?sequencia=<acordes separados por vírgula>` e faz `$http.get`; o backend
remove as vírgulas e devolve a primeira página (até 100 músicas) do conjunto
pré-computado. A página não tem formulário de cadastro, não persiste nada, não
coloca a sequência na URL e não tem controles de paginação: mostra no máximo a
primeira página, reordenada no cliente por `-popularidade`. O seletor de gênero
usa a constante `GENEROS` do JavaScript (51 itens), não o endpoint `/generos` (52
itens; falta `R&B;`). Os resultados da sequência não têm a chave `diferenca`, então
o `ng-hide="music.diferenca.length"` da tela é sempre falso e todos os cartões da
página aparecem.

## 1. Rota e arquivos

`static/assets/js/routes.js:17-21`:

```js
.when('/porsequencia', {
  templateUrl: "templates/sequencia.html",
  controller: "SequenciaController",
  controllerAs: "Sequencia"
})
```

- URL: `#/porsequencia` (não há parâmetro de rota).
- Template: `static/templates/sequencia.html` (63 linhas).
- Controller: `static/assets/js/controllers/sequencia.js` (105 linhas),
  registrado como `SequenciaController` e exposto como `Sequencia`.
- O controller é incluído em `static/index.html:145`; o módulo Angular é
  `deciframeApp` (`static/assets/js/app.js:1-2`).
- A página é alcançada pelo cartão da home “Conheces alguma dessas sequências de
  acordes?” (`static/templates/home.html:79-85`).

Versões carregadas em `static/index.html`:

| Biblioteca | Linha |
|---|---|
| jQuery 1.11.3 | `static/index.html:126` |
| Bootstrap 3.3.6 (JS) | `static/index.html:128` |
| AngularJS 1.4.9 | `static/index.html:130` |
| `angular-route` 1.4.9 | `static/index.html:131` |
| `angular-animate` 1.4.9 | `static/index.html:132` |
| `angular-ui-bootstrap` 2.1.4 | `static/index.html:133-134` |
| `ngprogress` | `static/index.html:136` |

Não há build step; os arquivos são servidos como estão.

## 2. Controller

### 2.1 Estado inicial

`static/assets/js/controllers/sequencia.js:1` injeta
`$http, $window, ngProgressFactory, $anchorScroll, $location, GENEROS`.
`$anchorScroll` e `$location` não são usados no corpo do controller.

`static/assets/js/controllers/sequencia.js:32-45`:

| Campo | Linha | Valor inicial |
|---|---|---|
| `vm.sequenciasFamosas` | `32-37` | array com os 4 objetos `sequencia1`..`sequencia4` |
| `vm.minhaSequencia` | `38` | `{}` |
| `vm.isSearching` | `39` | `false` |
| `vm.showSearchResultsCount` | `40` | `false` |
| `vm.esfigeSpeech` | `41` | `""` |
| `vm.musics` | `42` | `[]` |
| `vm.generos` | `43` | `GENEROS` (constante) |
| `vm.meuGenero` | `44` | `""` |
| `vm.progressbar` | `45` | `ngProgressFactory.createInstance()` |

Os 4 objetos (`static/assets/js/controllers/sequencia.js:2-31`) têm a mesma
estrutura:

```js
var sequencia1 = {
  'index': 1,
  'acordes': [
    { 'acorde': 'Bm', 'cor': '#2E1C74' },
    ...
  ]};
```

- `index` é sempre `1` e não é lido em nenhum ponto do controller/template;
- `cor` é sempre `#2E1C74`;
- as 4 sequências são: `Bm G D A`, `C G Am F`, `Gm F`, `C C7 F Fm`
  (`static/assets/js/controllers/sequencia.js:2-31`).

Não há chamada `$http` no carregamento da página: os 4 cartões são exibidos
imediatamente, sem consultar o backend.

### 2.2 `temAcorde`

`static/assets/js/controllers/sequencia.js:47-53`:

```js
vm.temAcorde = function(acorde) {
  if (vm.minhaSequencia.acordes) {
    return (vm.minhaSequencia.acordes.indexOf(acorde) > -1);
  } else {
    return false;
  }
}
```

O template passa o **objeto** `acordeon` (não a string). Como
`vm.minhaSequencia.acordes` é o mesmo array do cartão selecionado, o `indexOf`
por identidade encontra o objeto e retorna `true` para os acordes daquele cartão;
para os outros cartões, retorna `-1`. Efeito visual: o cartão selecionado fica
com os hexágonos “checados” (brancos); os demais não.

### 2.3 `createChordsString`

`static/assets/js/controllers/sequencia.js:55-61`:

```js
var createChordsString = function(chords) {
  var str = "";
  for (var i = 0; i < chords.length; i++) {
    str = str.concat(chords[i].acorde, ',');
  }
  return str.substring(0, str.length-1);
}
```

Junta os acordes com vírgula e remove a última. Para os 4 cartões:

| Cartão | String gerada | Chave no backend |
|---|---|---|
| `Bm G D A` | `Bm,G,D,A` | `BmGDA` (vírgulas removidas em `main.py:191`) |
| `C G Am F` | `C,G,Am,F` | `CGAmF` |
| `Gm F` | `Gm,F` | `GmF` |
| `C C7 F Fm` | `C,C7,F,Fm` | `CC7FFm` |

### 2.4 `pesquisarPorSequencia`

`static/assets/js/controllers/sequencia.js:63-90`:

1. se recebeu `sequencia`, faz `vm.minhaSequencia = sequencia` (`64-66`);
2. `vm.progressbar.start()` (`67`);
3. `vm.esfigeSpeech = "Procurando músicas com base na sequencia..."` (`68`);
4. `vm.isSearching = true` (`69`);
5. `vm.musics = []` (`70`);
6. `var apiUrl = ""` (`72`);
7. monta `searchString = "similares?sequencia=" + createChordsString(...)`
   (`73`);
8. se `vm.meuGenero` não for `""` nem `null`, acrescenta
   `&generos=<valor>` (`74-76`);
9. `$http.get(apiUrl.concat(searchString))` (`77`);
10. no sucesso: `progressbar.complete()`, speech “Encontrei essas músicas”,
    `isSearching = false`, `showSearchResultsCount = true`, `musics = data`
    (`78-84`);
11. no erro: speech “Ops! Algo errado.”, `isSearching = false`,
    `showSearchResultsCount = false` (`85-89`). O erro **não** chama
    `progressbar.complete()`.

O `ng-change` do seletor de gênero chama `pesquisarPorSequencia()` **sem
argumento** (`static/templates/sequencia.html:28`), então a sequência atual é
mantida (`64-66` só troca se receber argumento).

### 2.5 `limparPesquisa`

`static/assets/js/controllers/sequencia.js:92-95`:

```js
vm.limparPesquisa = function() {
  vm.minhaSequencia = {};
  vm.musics = [];
}
```

Zera a sequência e os resultados. Não zera `vm.meuGenero`, `vm.esfigeSpeech`
nem `vm.showSearchResultsCount`.

### 2.6 `goToLirics` e `goToResults`

- `vm.goToLirics(music)` (`static/assets/js/controllers/sequencia.js:97-99`) faz
  `$window.open(music.url)`; a URL vem de `musica.py:22`
  (`http://www.cifraclub.com.br/<id_artista>/<id_musica>`).
- `vm.goToResults()` (`static/assets/js/controllers/sequencia.js:101-104`) faz
  `showSearchResultsCount = false` e
  `$("body").animate({scrollTop: $("#results").offset().top}, "slow")` — usa
  jQuery, não `$anchorScroll`.

### 2.7 `isSearching`

`vm.isSearching` é definido (`static/assets/js/controllers/sequencia.js:39`) e
atualizado (`69`, `81`, `87`), mas **não é lido** em
`static/templates/sequencia.html` (grep no template). Não há indicador visual
ligado a ele.

## 3. Template

`static/templates/sequencia.html` tem dois painéis:

| Painel | Linhas | Conteúdo |
|---|---|---|
| Esquerdo (`viewWindow-panel-C`) | `3-16` | título, 4 cartões, botão flutuante |
| Direito (`viewWindow-panel-D`, `id="results"`) | `17-62` | sequência selecionada + resultados |

### 3.1 Cartões

`static/templates/sequencia.html:5-8`:

```html
<h4 class="text-center">Aponte uma sequencia de acordes</h4>
<div class="acordes-container" ng-repeat='sequencia in Sequencia.sequenciasFamosas' ng-click="Sequencia.pesquisarPorSequencia(sequencia)">
  <df-hex acorde="{{acordeon.acorde}}" acorde-color="{{acordeon.cor}}" acorde-checked="Sequencia.temAcorde(acordeon)" ng-repeat="acordeon in sequencia.acordes"></df-hex>
</div>
```

- `ng-repeat` sobre os 4 objetos; cada cartão é um `div.acordes-container`;
- `ng-click` chama `pesquisarPorSequencia(sequencia)`;
- cada acorde é um `<df-hex>` com `acorde`, `acorde-color` e
  `acorde-checked` (resultado de `temAcorde`);
- o título não tem acento em “sequencia”.

### 3.2 Botão flutuante

`static/templates/sequencia.html:10-14`:

```html
<button class="search-results-count" ng-if="Sequencia.showSearchResultsCount" ng-click="Sequencia.goToResults()">
  <span class="glyphicon glyphicon-triangle-bottom bounce animated infinite"></span>
  <br>
  Encontrei essas músicas
</button>
```

- só aparece quando `showSearchResultsCount` é `true` (sucesso da busca);
- o texto é fixo (“Encontrei essas músicas”), sem contagem;
- `static/assets/css/app.css:427-448` posiciona o botão como `position: fixed` no rodapé e o
  esconde em telas `>= 768px` (`@media (min-width: 768px) { .search-results-count { display: none; } }`);
- `goToResults` rola até `#results`.

### 3.3 Bloco da sequência selecionada

`static/templates/sequencia.html:19-38`:

```html
<div ng-show="Sequencia.minhaSequencia.acordes.length">
  <h4>{{Sequencia.esfigeSpeech}}</h4>
  ...
  <select ... ng-options="genero for genero in Sequencia.generos | orderBy:'genero'"
          ng-model="Sequencia.meuGenero"
          ng-change="Sequencia.pesquisarPorSequencia()">
    <option value="">-- Gênero --</option>
  </select>
  ...
  <df-hex acorde="{{acordeon.acorde}}" acorde-color="{{acordeon.cor}}"
          ng-repeat="acordeon in Sequencia.minhaSequencia.acordes"
          ng-click="Sequencia.limparPesquisa()"></df-hex>
</div>
```

- o bloco só aparece quando `minhaSequencia.acordes.length` é verdadeiro; com
  `minhaSequencia = {}`, o acesso é null-safe no Angular 1.4.9 e o bloco fica
  oculto;
- o `h4` mostra `esfigeSpeech` (“Procurando...” / “Encontrei...” / “Ops!...”);
- o `<select>` usa `GENEROS` (constante) e `ng-change` refaz a busca;
- os hexágonos da sequência selecionada não têm `acorde-checked`, então usam a
  cor padrão; clicar em qualquer um chama `limparPesquisa()`.

### 3.4 Resultados

`static/templates/sequencia.html:40-59`:

```html
<div class="row row-in">
  <div class="col-sm-6 col-lg-4"
    ng-repeat="music in Sequencia.musics | orderBy:'-popularidade'"
    ng-hide="music.diferenca.length">

      <div class="music-card" ng-click="Sequencia.goToLirics(music)">
        ...
        <p class="music-title">{{music.nome_musica}}</p>
        <p class="music-artist">{{music.nome_artista}}</p>
        <p class="music-gender"><span class="label label-default">{{music.genero}}</span></p>
        ...
      </div>

  </div>
</div>
```

- `ng-repeat` sobre `musics`, ordenado no cliente por `-popularidade`;
- `ng-hide="music.diferenca.length"`: os objetos do modo sequência **não têm**
  `diferenca` (`main.py:210-220`), então a expressão é `undefined` e o
  `ng-hide` é falso; todos os cartões da página aparecem. O Angular 1.4.9 é
  null-safe para acesso a membro (`music.diferenca.length` não lança quando
  `music.diferenca` não existe);
- cada cartão mostra `nome_musica`, `nome_artista` e `genero`;
- clicar no cartão abre `music.url` em nova janela (`goToLirics`);
- não há seção de `diferenca`/`intersecao` nem hexágonos de “aprender mais”,
  diferente de `static/templates/acordes.html:61-91` e
  `static/templates/musica.html:83-113`, que usam `ng-show="music.diferenca.length"`
  e renderizam `music.diferenca`.

## 4. As 4 sequências do frontend vs as 6 do backend

| Índice no backend | Chave | Frontend |
|---|---|---|
| 0 | `BmGDA` | `sequencia1`: `Bm G D A` |
| 1 | `CGAmF` | `sequencia2`: `C G Am F` |
| 2 | `EmG` | **ausente** |
| 3 | `CA7DmG7` | **ausente** |
| 4 | `GmF` | `sequencia3`: `Gm F` |
| 5 | `CC7FFm` | `sequencia4`: `C C7 F Fm` |

Fontes: `static/assets/js/controllers/sequencia.js:2-31` e
`main.py:40-45`. O arquivo `data/mapeamento_sequencias_famosas.txt:1-6` lista os
rótulos dos 6 índices, mas não é lido por nenhum código.

Consequência descritiva: as sequências `EmG` e `CA7DmG7` existem no backend
(4 e 5 músicas, respectivamente) e não têm cartão na página; as 4 que têm cartão
são exatamente as que o backend indexa como 0, 1, 4 e 5.

## 5. Requisição e resposta

### 5.1 URL

- `apiUrl = ""` (`static/assets/js/controllers/sequencia.js:72`), então a
  requisição é relativa à origem;
- a constante `RESTAPI` (`static/assets/js/app.js:3-5`, com
  `url: 'http://localhost:5003'`) **não é usada** por este controller;
- a URL final é `similares?sequencia=<acordes>` e, opcionalmente,
  `&generos=<gênero>` (`static/assets/js/controllers/sequencia.js:73-76`);
- não há `pagina` na URL.

### 5.2 Contrato do backend

`main.py:190-197` remove as vírgulas e faz lookup exato; `main.py:203-223`
devolve uma lista de objetos com 9 chaves (`main.py:210-220`):
`id_unico_musica`, `id_artista`, `id_musica`, `nome_artista`, `nome_musica`,
`popularidade`, `acordes`, `genero`, `url`.

`main.py:226-228` fatia a primeira página (até 100, `main.py:35`), porque
`pagina` default é `'1'` (`main.py:176`). A resposta é `json.dumps`
(`main.py:197`), com `Content-Type: text/html; charset=utf-8` (observado).

### 5.3 O que a página mostra

Como não envia `pagina`, a página recebe no máximo 100 músicas. Com os dados
atuais:

| Sequência | Total no backend | Páginas | O que a página mostra |
|---|---:|---:|---|
| `BmGDA` | 199 | 2 | no máximo 100 |
| `CGAmF` | 296 | 3 | no máximo 100 |
| `GmF` | 7 | 1 | 7 |
| `CC7FFm` | 3 | 1 | 3 |

As sequências `EmG` e `CA7DmG7` não são acessíveis pela página (não há cartão).
Não há botão “próxima página” nem `pagina` na URL.

## 6. Filtro de gênero

- `vm.generos = GENEROS` (`static/assets/js/controllers/sequencia.js:43`);
- `GENEROS` é uma constante com 51 strings (`static/assets/js/app.js:6-58`);
- o `<select>` usa `ng-options="genero for genero in Sequencia.generos | orderBy:'genero'"`
  (`static/templates/sequencia.html:24-30`), com a opção vazia
  `-- Gênero --`;
- `ng-change="Sequencia.pesquisarPorSequencia()"` refaz a busca com a sequência
  atual;
- o valor escolhido é concatenado cru em `&generos=<valor>`
  (`static/assets/js/controllers/sequencia.js:74-76`); o backend faz
  `generos_tag.split(',')` (`main.py:181-182`) e `apply_filtro`
  (`main.py:266-272`) ignora gêneros que não existem em `generos`.

O endpoint `/generos` devolve 52 gêneros; a constante tem 51. O único gênero do
CSV ausente da constante é `R&B;` (303 músicas). A página não consulta
`/generos`.

## 7. O que a página não tem

| Ausência | Evidência |
|---|---|
| Cadastro de sequência | não há `<form>`, `<input>` nem botão de salvar em `static/templates/sequencia.html`; `vm.minhaSequencia` só é atribuído em `static/assets/js/controllers/sequencia.js:65` (clique no cartão) ou zerado em `:93` |
| Persistência no navegador | não há `localStorage`/`sessionStorage` no controller (grep) |
| Sequência na URL | a rota é `#/porsequencia`, sem parâmetro (`static/assets/js/routes.js:17-21`) |
| Paginação | a URL não tem `pagina` (`static/assets/js/controllers/sequencia.js:73-76`); o template não tem controle de próxima/anterior |
| Serviço/factory de API | o controller usa `$http` diretamente (`static/assets/js/controllers/sequencia.js:77`) |
| Uso de `RESTAPI` | a constante existe (`static/assets/js/app.js:3-5`) mas não é referenciada no controller |
| Indicador de `isSearching` | `vm.isSearching` é atualizado (`static/assets/js/controllers/sequencia.js:39,69,81,87`) mas não aparece no template |
| Uso de `$anchorScroll`/`$location` | injetados (`static/assets/js/controllers/sequencia.js:1`) mas não usados; o scroll é jQuery (`:103`) |

## 8. Diretiva `df-hex` e CSS

### 8.1 Diretiva

`static/assets/js/directives/df-hex.js:1-12`:

```js
angular.module('deciframeApp').directive('dfHex', function() {
  return {
    restrict: 'E',
    scope: {
      acorde: '@',
      acordeColor: '@',
      acordeChecked: '=',
      small: '='
    },
    templateUrl: 'templates/directives/df-hex.html'
  }
});
```

O template (`static/templates/directives/df-hex.html:1-9`) desenha um SVG
hexagonal e o texto do acorde; quando `acordeChecked` é verdadeiro, o preenchimento
vira `#FFF` e o texto `#474747`; caso contrário, usa `acordeColor`.

### 8.2 CSS

| Seletor | Linha | Efeito |
|---|---|---|
| `.viewWindow-panel-C` | `static/assets/css/app.css:79` | fundo rosa `#BA007C`, texto branco (painel esquerdo) |
| `.viewWindow-panel-D` | `static/assets/css/app.css:80` | fundo branco, texto `#333` (painel direito) |
| `.acordes-container` | `static/assets/css/app.css:161` | container dos cartões |
| `.music-card` | `static/assets/css/app.css:263-272` | cartão de resultado |
| `.search-results-count` | `static/assets/css/app.css:427-448` | botão fixo no rodapé; oculto em `>= 768px` |

## 9. Fluxo completo

```
Usuário abre #/porsequencia
  └─ routes.js:17-21 → sequencia.html + SequenciaController
       └─ controller: 4 cartões hardcoded (sequencia.js:2-37), sem $http
Usuário clica num cartão
  └─ ng-click → pesquisarPorSequencia(sequencia) (sequencia.html:6)
       ├─ minhaSequencia = sequencia (sequencia.js:65)
       ├─ createChordsString → "Bm,G,D,A" (sequencia.js:55-61)
       ├─ GET similares?sequencia=Bm,G,D,A[&generos=...] (sequencia.js:73-77)
       └─ backend: main.py:190-197 → main.py:203-223 → main.py:226-228
            └─ 9 chaves por música, até 100 (main.py:35)
Usuário recebe a resposta
  └─ success: musics = data; speech "Encontrei essas músicas";
     showSearchResultsCount = true (sequencia.js:78-84)
       └─ template: ng-repeat musics | orderBy:'-popularidade'
          (sequencia.html:42); ng-hide="music.diferenca.length" (sequencia.html:43)
Usuário clica num resultado
  └─ goToLirics → window.open(music.url) (sequencia.js:97-99; musica.py:22)
Usuário troca o gênero
  └─ ng-change → pesquisarPorSequencia() (sequencia.html:28)
Usuário clica num hexágono da sequência selecionada
  └─ limparPesquisa → minhaSequencia = {}; musics = [] (sequencia.js:92-95)
```

## 10. Referências de código

| Assunto | Referência |
|---|---|
| Rota | `static/assets/js/routes.js:17-21` |
| Inclusão do controller | `static/index.html:145` |
| Versões | `static/index.html:126-136` |
| 4 sequências | `static/assets/js/controllers/sequencia.js:2-31` |
| Estado inicial | `static/assets/js/controllers/sequencia.js:32-45` |
| `temAcorde` | `static/assets/js/controllers/sequencia.js:47-53` |
| `createChordsString` | `static/assets/js/controllers/sequencia.js:55-61` |
| Busca | `static/assets/js/controllers/sequencia.js:63-90` |
| `limparPesquisa` | `static/assets/js/controllers/sequencia.js:92-95` |
| `goToLirics` | `static/assets/js/controllers/sequencia.js:97-99` |
| `goToResults` | `static/assets/js/controllers/sequencia.js:101-104` |
| Cartões | `static/templates/sequencia.html:5-8` |
| Botão flutuante | `static/templates/sequencia.html:10-14` |
| Bloco selecionado | `static/templates/sequencia.html:19-38` |
| Seletor de gênero | `static/templates/sequencia.html:24-30` |
| Resultados | `static/templates/sequencia.html:40-59` |
| `GENEROS` | `static/assets/js/app.js:6-58` |
| `RESTAPI` (não usado) | `static/assets/js/app.js:3-5` |
| Diretiva `df-hex` | `static/assets/js/directives/df-hex.js:1-12` |
| Template `df-hex` | `static/templates/directives/df-hex.html:1-9` |
| CSS do painel | `static/assets/css/app.css:79-80` |
| CSS do botão | `static/assets/css/app.css:427-448` |
| Link da home | `static/templates/home.html:79-85` |
| Backend da sequência | `main.py:190-197`, `main.py:203-223` |
| Paginação | `main.py:226-228`, `main.py:35`, `main.py:176` |
| URL do Cifra Club | `musica.py:22` |
| Rótulos dos índices | `data/mapeamento_sequencias_famosas.txt:1-6` |
