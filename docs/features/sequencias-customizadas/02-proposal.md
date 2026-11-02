# Proposta — Sequências de Acordes Customizadas

## Abordagem escolhida

### Algoritmo de matching

**Matcher único em tempo real com o predicado histórico (mais
alinhado).** Substituir o teste da tag por um matcher calculado sobre
`musica.cifra` que reproduz exatamente “contígua ∧ subconjunto”; as 6 originais
e as novas passam pelo mesmo caminho, com as 6 semeadas no banco.

Novo módulo/funções de matching (`contiguous`, `vocab_subset`,
case-insensitive); `get_similares_por_sequencia` carrega a sequência do banco e
chama o matcher em vez de testar `str(id_seq) in musica.seqs_famosas`;
`/similares` resolve a chave/id no banco. `SEQ_FAMOSA` permanece só como oráculo
de regressão.

Benefícios: reprodução exata de 199/296/4/5/7/3, semântica uniforme, sem
dependência nova. Riscos: varredura O(67k músicas × tamanho da sequência) por
busca, sem índice, ordem de páginas dependente de `PYTHONHASHSEED` e variações
de escrita de acorde continuam distintas.

Validar comparando conjuntos de `id_unico_musica` com os 6 golden sets,
percorrendo todas as páginas e sem duplicatas; cobrir ordem, repetição e acordes
extras; testar contrato de 9 chaves, `Content-Type: text/html` e 100 por página;
medir tempo de resposta com o catálogo cheio.

### Banco de dados

**SQLite + volume nomeado (mais alinhado).** Usar SQLite (stdlib)
para o catálogo em um caminho dedicado, por exemplo `/app/db/sequences.db`, com
volume nomeado montado em `/app/db`; criar schema e semear as 6 no startup. O
CSV de músicas/gêneros fica intacto.

Novo `db.py` com `init_db`, `list_sequences`, `create_sequence` e
`get_sequence`; `main.py` chama `init_db()` antes de servir e semeia as 6;
`Dockerfile` declara `VOLUME ["/app/db"]` (ou o README passa
`-v ciframe-db:/app/db`); `README.md` e `AGENTS.md` são atualizados.

Benefícios: ACID, constraints, índice único, consultas SQL, stdlib, sem
dependência nova, container único e persistência robusta com volume. Riscos:
schema/migrations, concorrência do SQLite, escolha do caminho para não sombrear
o CSV e a mudança no comando `docker run` precisa ser documentada.

Validar criação, `docker stop/start` e `docker rm` + novo `run` com o mesmo
volume; sem volume, confirmar a perda; regressão 6/6; CRUD e busca;
duplicatas/inválidos; queries parametrizadas e escrita concorrente.

### Esquema de dados (alto nível)

O schema proposto é `sequences`, com os acordes em `sequence_chords` posicional
ou JSON de acordes, e chave única normalizada. O banco é inicializado no startup
e semeia as 6 sequências.

Ainda precisam de decisão: acordes em coluna JSON ou tabela filha; política de
duplicatas (case-sensitive ou normalizada); migrations, backup e versionamento
do schema; caminho `/app/db` ou `/app/instance`; e volume nomeado ou bind mount.

### API

Adicionar `GET /sequencias` e `POST /sequencias`; `/similares` resolve o
catálogo no banco. O catálogo é aberto e anônimo, conforme o requisito. Os
endpoints continuam retornando `json.dumps(...)`.

Ainda precisam de decisão: formato exato de `GET`/`POST /sequencias`; identidade
da sequência na busca (id ou string de acordes); política de duplicatas e
normalização; limite de tamanho, sequência vazia e acordes inválidos.

### Frontend

**Catálogo dinâmico + formulário inline na própria página (mais
alinhado).** Substituir os 4 objetos hardcoded por `GET /sequencias`, renderizar
os cartões a partir do catálogo e adicionar um formulário inline na própria
`#/porsequencia` para `POST /sequencias`; após salvar, atualizar o catálogo e
selecionar a nova sequência.

`sequencia.js` remove `sequencia1`..`sequencia4`, adiciona
`carregarSequencias()` e `criarSequencia()`, mapeia os acordes da API para
`{acorde, cor}` e mantém `pesquisarPorSequencia()` e `createChordsString()`.
`sequencia.html` troca o `ng-repeat` de `sequenciasFamosas` pelo catálogo da API
e adiciona o formulário, mantendo o bloco selecionado e os resultados.
`routes.js` não muda; ainda é preciso decidir se `GENEROS` vira `/generos`.

Benefícios: menor mudança, reutiliza `df-hex`, CSS e fluxo de busca. Riscos: a
página não tem paginação, o catálogo pode crescer e poluir a tela, validação e
duplicatas ficam no formulário, e `GENEROS` está desatualizado (51 vs 52).

Validar com testes de controller/serviço com `$http` mockado, integração
`GET`/`POST /sequencias`, E2E carregando o catálogo, cadastrando, buscando e
vendo resultados, regressão das 6, limite de 100 e o vídeo/gif exigido.

## Alternativas consideradas e descartadas

**Matching — caminho duplo:** manter a tag para as 6 e usar matcher mais
permissivo para as novas dá zero risco de regressão e busca rápida para as 6,
mas cria duas semânticas; uma cópia customizada de `BmGDA` pode divergir da
original. Também atende menos ao requisito “exatamente do mesmo jeito”.

**Banco — catálogo JSON + escrita atômica + bind mount:** código mínimo, sem
schema/migrations e fácil de inspecionar/editar, mas sem ACID/constraints, com
concorrência de escrita, validação de duplicatas no código e evolução de formato
sem migrations.

**Frontend — rota/modal dedicada com chord builder e autocomplete:** UX melhor,
autocomplete, preview e separação entre cadastro e busca, mas mais código,
rotas, templates e testes; pode ser over-scope no AngularJS 1.4.9 legado.

## Escopo explícito

**Dentro do escopo:**

- Catálogo persistido de sequências; músicas e gêneros continuam no CSV em
  memória.
- As seis sequências originais sem regressão.
- Container Docker único e local, sem serviços externos adicionais.
- Catálogo dinâmico e cadastro em `#/porsequencia`.
- Validação por golden sets (199/296/4/5/7/3; total 514), comparando conjuntos,
  não ordem; persistência, API e UI.

**Fora do escopo (e por quê):**

- Migração de músicas e gêneros para o banco: o requisito fixa CSV em memória.
- PostgreSQL, MySQL, Redis e MongoDB: exigem serviço externo adicional.
- Autocomplete, chord builder, rota/modal dedicada, paginação de catálogo e
  paginação de resultados: não são decididos pela pesquisa e ampliam o escopo.
