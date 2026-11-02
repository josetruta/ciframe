# Sequências de Acordes Customizadas — Design Document / Plano

> Plano derivado das quatro pesquisas em `research/` e da Proposta registrada em
> `02-proposal.md`. Não implementa nenhuma mudança: é o roteiro da fase de
> implementação. Estrutura espelhada de
> `~/reppit-framework/templates/design_doc_template.md` (template do RePPIT).
>
> **Premissas deste plano (confirmar antes da Fase 1):** escopo limitado à
> Proposta 1 (matcher único, SQLite + volume, catálogo dinâmico + formulário
> inline); sem autocomplete, sem paginação de catálogo/resultados, sem
> normalização além de lowercase e sem serviço externo. Timeline são estimativas
> relativas, não prazos acordados.

> Este documento foi preenchido pelo agente ao executar o comando /make-plan.
> Não sei se era o objetivo do step (ou se era algo a ser preenchido manualmente),
> mas optei por deixar duas versões: uma preenchida pelo agente e que foi utilizada
> nos steps posteriores; e uma preenchida por mim, inspirado no passo de make-plan
> e no documento gerado pelo agente.

## Contexto Atual

- Aplicação Flask + AngularJS 1.4.9 servida em um único container Docker local
  (`docs/adr/0001-local-only-docker-deploy.md`). O catálogo de músicas/gêneros é
  lido uma vez do CSV `data/top/dataset_final.csv` no import (`main.py:49-98`) e
  mantido em memória; não há banco de dados.
- As 6 sequências atuais são um dicionário fixo em `main.py:40-45`. A busca
  `/similares?sequencia=` remove as vírgulas, faz lookup exato nesse dicionário e
  devolve as músicas cujo `seqs_famosas` contém o índice (`main.py:190-197`,
  `main.py:203-223`).
- A tag `seqs_famosas` é pré-computada por `get_famosas`
  (`scripts/generate_data_set.py:7-24`): bloco contíguo case-insensitive **e**
  vocabulário da música ⊆ vocabulário da sequência. A ordem importa; repetição
  não. O runtime não normaliza acordes (`main.py:11-23`).
- `Musica` já expõe a lista ordenada com repetição em `cifra` e o conjunto em
  `acordes` (`musica.py:16-17`), que é o que o matcher em tempo real precisa.
- A página `#/porsequencia` tem 4 cartões hardcoded (`sequencia.js:2-31`), sem
  cadastro, persistência, parâmetro de URL ou paginação; a busca mostra no máximo
  a primeira página de 100 (`sequencia.js:63-90`, `main.py:35`).
- O `Dockerfile` não declara `VOLUME` (`Dockerfile:1-12`) e o `docker run` do
  README não monta volume (`README.md:15-18`). `stop`/`start` do mesmo container
  preserva a camada gravável; `rm` + novo `run` perde o que foi escrito nela.
- **Dores:** sequências novas não podem ser cadastradas; a tag não existe para
  elas; o catálogo não persiste; a UI não reflete o backend; e as 6 originais
  precisam continuar com os mesmos resultados.

## Requisitos

### Requisitos Funcionais

- **RF1 — Cadastro anônimo:** qualquer visitante pode cadastrar uma sequência
  ordenada de acordes, sem login, com validação de entrada.
- **RF2 — Catálogo persistido:** o catálogo de sequências sobrevive a reinícios
  do processo e a `docker stop`/`start`; com volume, sobrevive a `docker rm` +
  novo `docker run`.
- **RF3 — Busca unificada:** qualquer sequência do catálogo (as 6 originais ou
  uma nova) pode ser usada em `/similares`, com o mesmo formato de resultado.
- **RF4 — Regressão das 6:** as 6 originais mantêm exatamente os conjuntos de
  músicas de hoje: 199, 296, 4, 5, 7 e 3 (total 514), comparados como conjunto,
  não como ordem de página.
- **RF5 — Catálogo na UI:** `#/porsequencia` carrega o catálogo real do backend,
  exibe as 6 originais e as novas, e permite selecionar qualquer uma para busca.
- **RF6 — Cadastro na UI:** a mesma página permite cadastrar uma sequência e,
  após o sucesso, atualizar o catálogo e selecionar a nova sequência.
- **RF7 — Compatibilidade:** os endpoints existentes continuam retornando
  `json.dumps(...)` (não `jsonify`) e o formato atual dos resultados de
  sequência (campos, 100 por página, `Content-Type: text/html`).
- **RF8 — Seed:** em banco novo, as 6 originais são semeadas automaticamente e
  aparecem no catálogo.

### Requisitos Não Funcionais

- **RNF1 — Simplicidade operacional:** um único container; sem PostgreSQL,
  MySQL, Redis, MongoDB ou outro serviço/rede adicional.
- **RNF2 — Dependências:** nenhuma dependência nova de runtime; usar a stdlib
  (`sqlite3`, `json`, `os`, `unittest`).
- **RNF3 — Desempenho:** a busca por sequência continua varrendo o catálogo em
  memória como hoje (`main.py:236-245`); medir o tempo com o CSV completo e
  manter o comportamento aceitável para uso local. Não há índice nesta fase.
- **RNF4 — Integridade:** chave única normalizada impede duplicatas exatas;
  escritas usam queries parametrizadas.
- **RNF5 — Observabilidade:** não há logging/métricas no app; a única exigência
  é falhar rápido e com mensagem clara no startup se o banco não puder ser
  aberto/criado.
- **RNF6 — Segurança:** catálogo é aberto e anônimo por requisito; validar
  tamanho/formato dos acordes e não interpolar SQL. Rate limiting, moderação e
  autenticação ficam fora do escopo.
- **RNF7 — Portabilidade local:** o caminho padrão do banco é relativo
  (`db/sequences.db`), funcionando no virtualenv e, com `WORKDIR /app`, em
  `/app/db` no container; `DECIFRAME_DB` permite sobrescrever.

## Decisões de Design

### 1. Matching: predicado único em tempo real

**Decisão:** implementar o matcher calculado sobre `musica.cifra` que reproduz
exatamente o predicado histórico — bloco contíguo case-insensitive **e**
`set(musica.cifra) ⊆ set(sequencia)` — e usá-lo para todas as sequências. A tag
`seqs_famosas` deixa de ser fonte de verdade em runtime e permanece apenas como
oráculo de regressão.

- **Regra exata:** `contigua(cifra, seq, case_insensitive=True)` e
  `vocabulario_da_musica_contido_na_sequencia(cifra, seq)`; a música casa se
  ambas forem verdadeiras. A ordem da sequência é preservada; repetições na
  música não invalidam; repetições na sequência são tratadas como lista (o
  predicado histórico usa a string com `;`, então a ordem e a multiplicidade da
  sequência importam).
- **Normalização:** somente lowercase, como a tag. Não haverá normalização de
  sufixos, enarmônicos ou grafias alternativas nesta fase.
- **Identidade:** o `id` inteiro do banco é a identidade canônica na API. O
  endpoint mantém um alias legado para as 6: `?sequencia=Bm,G,D,A` (ou
  `?sequencia=BmGDA`) resolve para o `id` semeado. A UI passa a enviar `id`.
- **Duplicatas:** `normalized_key` única (acordes em lowercase unidos por `,`).
  `POST` de sequência já existente retorna `409` com o `id` existente; a UI
  seleciona a existente. Isso também impede uma cópia customizada de `BmGDA`
  divergir da original.
- **Por quê:** é o único predicado medido que reproduz as 6 tags
  (`research/01-matching-semantica.md` §§3–4;
  `research/02-validacao-hipotese.md` §§2–3). Semântica única, sem caminho
  especial, sem dependência nova.
- **Trade-offs:** varredura O(67k músicas × tamanho da sequência) por request;
  sem índice; ordem de páginas dependente de `PYTHONHASHSEED` (comparar
  conjuntos); grafias alternativas continuam distintas. O modo `acordes` já
  varre o catálogo (`main.py:236-245`), então o padrão de custo é conhecido.

### 2. Persistência: SQLite + volume nomeado

**Decisão:** SQLite (stdlib `sqlite3`) em `db/sequences.db` (no container,
`/app/db/sequences.db`), com volume nomeado `ciframe-db` montado em `/app/db`.
O CSV de músicas/gêneros continua em memória.

- **Schema:** uma tabela `sequences` com `id`, `chords_json`, `normalized_key`
  única e `created_at`. Acordes ficam em JSON ordenado em uma coluna; não haverá
  tabela filha nesta fase (simplicidade; o catálogo é pequeno).
- **Inicialização:** `init_db()` cria a tabela com `CREATE TABLE IF NOT EXISTS` e
  semeia as 6 originais com `INSERT OR IGNORE`; roda no import de `main.py`,
  antes de atender requests.
- **Caminho:** `DB_PATH = os.environ.get("DECIFRAME_DB", os.path.join("db",
  "sequences.db"))`; `os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)`.
  Isso evita montar volume em `/app/data`, que sombrearia o CSV.
- **Conexões:** abrir/fechar uma conexão por operação, com `timeout=10`; sem
  conexão global compartilhada. Com o gunicorn em 1 worker (default), não é
  necessário WAL nesta fase.
- **Por quê:** ACID, constraint única, consultas SQL, stdlib, sem serviço
  externo e persistência robusta com volume (`research/03-banco-de-dados.md`
  §§3–6).
- **Trade-offs:** schema/migrations simples; concorrência limitada se o número
  de workers aumentar; necessidade de documentar o volume; `.dockerignore`
  precisa excluir o banco local para não cozinhá-lo na imagem.

### 3. API: catálogo e busca por id

**Decisão:** adicionar `GET /sequencias` e `POST /sequencias`; adaptar
`/similares` para resolver `id` (ou alias legado) no banco. Todos continuam
retornando `json.dumps(...)`.

- **`GET /sequencias`:** retorna `[{"id": 1, "acordes": ["Bm", "G", "D", "A"]},
  ...]`, ordenado por `id` (6 originais primeiro, depois as novas).
- **`POST /sequencias`:** corpo `{"acordes": ["Bm", "G", "D", "A"]}`; valida
  lista não vazia, até 20 acordes, cada um com 1–20 caracteres; `201` com o
  objeto criado; `400` para payload inválido; `409` para duplicata com o `id`
  existente.
- **`/similares`:** se `sequencia` for numérico, busca por `id`; senão, tenta o
  alias legado das 6; sequência inexistente devolve `[]` como hoje. O filtro
  `generos` e a paginação `pagina`/`TAM_PAGINA=100` permanecem.
- **Contrato:** os resultados de sequência mantêm os campos atuais
  (`id_unico_musica`, `id_artista`, `id_musica`, `nome_artista`, `nome_musica`,
  `popularidade`, `acordes`, `genero`, `url`) e **não** incluem `diferenca`.
- **Por quê:** separa catálogo de busca, permite a UI carregar/atualizar cartões
  e mantém o formato de resposta que a página já consome.

### 4. Frontend: catálogo dinâmico + formulário inline

**Decisão:** substituir os 4 objetos hardcoded por `GET /sequencias` e adicionar
um formulário inline na própria `#/porsequencia` para `POST /sequencias`.

- **Cartões:** `vm.sequencias` recebe o catálogo da API; cada acorde é mapeado
  para `{acorde, cor}` com a cor atual `#2E1C74`; o `ng-repeat` do template usa
  `Sequencia.sequencias`.
- **Cadastro:** input de texto simples no formato `Bm, G, D, A`; o controller
  divide por vírgula/espaço, remove vazios, valida e envia `{acordes: [...]}`.
  Não haverá chips, autocomplete ou editor dedicado nesta fase.
- **Após criar:** recarregar o catálogo e chamar `pesquisarPorSequencia` na nova
  sequência; em `409`, mostrar mensagem e selecionar a existente; em `400`,
  mostrar o erro.
- **Busca:** `pesquisarPorSequencia` usa `sequencia.id` em
  `similares?sequencia=<id>`; o filtro de gênero e a barra de progresso
  continuam.
- **Não muda:** `routes.js`, `index.html`, `app.js`/`GENEROS`, o bloco de
  resultados e o `ng-hide="music.diferenca.length"` (resultados de sequência não
  têm `diferenca` e continuam aparecendo). A página continua sem paginação e
  mostra no máximo 100 resultados; isso é uma limitação conhecida, não um item
  desta fase.

### 5. Fora do escopo

- Migrar músicas/gêneros para o banco (o requisito fixa CSV em memória).
- PostgreSQL/MySQL/Redis/MongoDB e qualquer serviço externo.
- Autocomplete, chord builder, rota/modal dedicada, edição/exclusão, moderação,
  rate limiting, paginação de catálogo/resultados, normalização de grafias e
  correção da constante `GENEROS` (51 vs 52; falta `R&B;`).
- Migrations versionadas/backup automático; nesta fase, apenas
  `CREATE TABLE IF NOT EXISTS` e seed idempotente.

## Design Técnico

### 1. Componentes Principais

```python
# matching.py (novo)
def contigua(cifra: list[str], sequencia: list[str]) -> bool: ...
def vocabulario_contido(cifra: list[str], sequencia: list[str]) -> bool: ...
def musica_casa_sequencia(cifra: list[str], sequencia: list[str]) -> bool: ...
```

```python
# db.py (novo)
DB_PATH: str
def init_db() -> None: ...
def listar_sequencias() -> list[dict]: ...
def criar_sequencia(acordes: list[str]) -> dict: ...  # levanta Duplicada
def buscar_sequencia(id_seq: int) -> dict: ...  # None se não existir
def buscar_por_alias_legado(chave: str) -> dict: ...  # None se não existir
```

- `main.py`: `init_db()` no startup; `GET/POST /sequencias`; `/similares`
  resolve `id`/alias e chama `get_similares_por_sequencia(acordes_seq,
  generos_key)`; a função passa a usar `matching.musica_casa_sequencia` em vez
  de `str(id_seq) in musica.seqs_famosas` (`main.py:209`).
- `musica.py`: sem mudança; `cifra` e `acordes` já existem (`musica.py:16-17`).
- `scripts/generate_data_set.py`: sem mudança; a tag continua no CSV e é usada
  como oráculo de regressão.
- Frontend: `sequencia.js` e `sequencia.html`; sem novos arquivos JS, sem build.

### 2. Modelos de Dados

```sql
CREATE TABLE IF NOT EXISTS sequences (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  chords_json TEXT NOT NULL,
  normalized_key TEXT NOT NULL UNIQUE,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
```

- `chords_json`: JSON array ordenado, ex. `["Bm","G","D","A"]`.
- `normalized_key`: acordes em lowercase unidos por `,`, ex. `bm,g,d,a`.
- Seed das 6: `BmGDA` (`bm,g,d,a`), `CGAmF` (`c,g,am,f`), `EmG` (`em,g`),
  `CA7DmG7` (`c,a7,dm,g7`), `GmF` (`gm,f`), `CC7FFm` (`c,c7,f,fm`).

**Contrato JSON:**

```json
// GET /sequencias
[{"id": 1, "acordes": ["Bm", "G", "D", "A"]}]

// POST /sequencias
{"acordes": ["Bm", "G", "D", "A"]}

// POST 201
{"id": 7, "acordes": ["Bm", "G", "D", "A"]}

// POST 409
{"erro": "sequencia ja existe", "id": 1}

// GET /similares?sequencia=1
[{"id_unico_musica": "...", "id_artista": "...", "id_musica": "...",
  "nome_artista": "...", "nome_musica": "...", "popularidade": 123,
  "acordes": ["..."], "genero": "...", "url": "..."}]
```

### 3. Pontos de Integração

- **Startup:** `main.py` importa o CSV (`main.py:49-98`) e chama `init_db()`; o
  seed das 6 roda antes de qualquer request. Falha de DB aborta o startup.
- **Fluxo de catálogo:** página → `GET /sequencias` → cartões; clique → `GET
  /similares?sequencia=<id>&generos=<...>` → resultados.
- **Fluxo de cadastro:** formulário → `POST /sequencias` → SQLite → recarrega
  `GET /sequencias` → seleciona a nova → busca.
- **Docker:** `VOLUME ["/app/db"]`; `docker run -v ciframe-db:/app/db ...`.
  O CSV continua em `/app/data/top/dataset_final.csv`; o volume não o sombreia.
- **Testes:** `DECIFRAME_DB` aponta para um arquivo temporário antes de importar
  `main`; a suíte usa o CSV real para os golden sets e não escreve no banco de
  desenvolvimento.

### 4. Arquivos Alterados

| Arquivo | Tipo | Mudança |
|---|---|---|
| `main.py` | modificado | `init_db`, rotas `GET/POST /sequencias`, resolução de `id`/alias em `/similares`, matcher no lugar da tag |
| `matching.py` | novo | predicado contíguo ∧ subconjunto, case-insensitive |
| `db.py` | novo | schema, seed, CRUD do catálogo, conexão SQLite |
| `Dockerfile` | modificado | `RUN mkdir -p /app/db`, `VOLUME ["/app/db"]` |
| `.dockerignore` | modificado | excluir `db/` e `*.db` do contexto de build |
| `.gitignore` | modificado | ignorar `db/` local |
| `README.md` | modificado | stack com SQLite; `docker run` com `-v ciframe-db:/app/db`; persistência |
| `AGENTS.md` | modificado | comando Docker com volume; gotcha do catálogo persistido |
| `static/assets/js/controllers/sequencia.js` | modificado | catálogo via API, formulário/criação, busca por `id` |
| `static/templates/sequencia.html` | modificado | cartões dinâmicos + formulário inline |
| `tests/test_matching.py` | novo | unidade do matcher |
| `tests/test_db.py` | novo | schema/seed/CRUD/duplicata |
| `tests/test_api.py` | novo | contrato, golden sets, paginação, alias legado |
| `docs/adr/0002-persist-custom-sequences.md` | modificado | registrar a decisão SQLite + volume (documentação da feature) |

> Nenhum outro arquivo deve ser alterado nesta fase. Em especial: `musica.py`,
> `scripts/generate_data_set.py`, `static/assets/js/app.js`, `routes.js`,
> `index.html`, `requirements.txt` e `data/top/*.csv` ficam intactos.

## Plano de Implementação

### Fase 1 — Fundações de matching e banco (1–1,5 dia)

- [ ] Extrair `contigua`, `vocabulario_contido` e `musica_casa_sequencia` de
  `research/scripts/validar_sequencias.py:86-106` para `matching.py`, com
  docstrings e tipos.
- [ ] Criar `tests/test_matching.py` cobrindo: bloco contíguo, ordem diferente,
  repetição na música, acordes extras, case-insensitive e sequência vazia.
- [ ] Criar `db.py` com `DB_PATH` configurável, `init_db`, `listar_sequencias`,
  `criar_sequencia`, `buscar_sequencia` e `buscar_por_alias_legado`.
- [ ] Implementar o schema `sequences` e o seed idempotente das 6; criar
  `tests/test_db.py` com banco temporário, duplicata e seed.
- [ ] Medir o custo do matcher com o CSV completo (67.585 músicas) e registrar o
  tempo no relatório de testes.

**Timeline:** 1–1,5 dia.

### Fase 2 — API e regressão (1 dia)

- [ ] Em `main.py`, chamar `init_db()` no startup e manter o carregamento do CSV
  intacto.
- [ ] Adicionar `GET /sequencias` e `POST /sequencias` com validação, `201`,
  `400` e `409`; retornar sempre `json.dumps`.
- [ ] Adaptar `/similares`: resolver `sequencia` numérica por `id`, alias legado
  para as 6, e chamar `get_similares_por_sequencia(acordes_seq, generos_key)`.
- [ ] Substituir `str(id_seq) in musica.seqs_famosas` (`main.py:209`) por
  `matching.musica_casa_sequencia(musica.cifra, acordes_seq)`.
- [ ] Criar `tests/test_api.py`: contrato dos endpoints, alias legado, 100 por
  página, 9 chaves e golden sets 199/296/4/5/7/3 (total 514), percorrendo todas
  as páginas e comparando conjuntos.
- [ ] Rodar `PYTHONHASHSEED=0 python3 -m unittest discover tests` e confirmar
  6/6 conjuntos iguais, 0 duplicatas e 0 faltantes.

**Timeline:** 1 dia.

### Fase 3 — Frontend (1 dia)

- [ ] Em `sequencia.js`, remover `sequencia1`..`sequencia4` (`:2-31`), criar
  `vm.sequencias`, `carregarSequencias()` e `criarSequencia()`; mapear acordes
  para `{acorde, cor: '#2E1C74'}`.
- [ ] Ajustar `pesquisarPorSequencia` para enviar `sequencia.id`; manter o filtro
  de gênero, a barra de progresso e o tratamento de erro.
- [ ] Adicionar estados de erro/sucesso do cadastro e, em `409`, selecionar a
  sequência existente.
- [ ] Em `sequencia.html`, trocar o `ng-repeat` de `sequenciasFamosas` (`:6`)
  por `Sequencia.sequencias` e adicionar o formulário inline; manter o bloco
  selecionado (`:19-38`) e os resultados (`:40-59`).
- [ ] Verificar manualmente: catálogo com as 6, cadastro de uma nova, duplicata,
  busca pela nova e pelas 6, limite de 100 e comportamento em mobile.

**Timeline:** 1 dia.

### Fase 4 — Persistência, Docker e documentação (0,5 dia)

- [ ] Atualizar `Dockerfile` com `RUN mkdir -p /app/db` e
  `VOLUME ["/app/db"]`.
- [ ] Atualizar `.dockerignore` (`db/`, `*.db`) e `.gitignore` (`db/`).
- [ ] Atualizar `README.md` e `AGENTS.md` com o novo `docker run` e a explicação
  do volume/persistência.
- [ ] Registrar a decisão em `docs/adr/0002-persist-custom-sequences.md`.
- [ ] Testar `docker build`, `docker run` com volume, `stop`/`start`, `rm` +
  novo `run` com o mesmo volume e o cenário sem volume (perda esperada).

**Timeline:** 0,5 dia.

### Fase 5 — Validação final e relatório (0,5 dia)

- [ ] Rodar a suíte completa e os golden sets; anexar tempos e contagens.
- [ ] Repetir o fluxo manual completo e gravar o vídeo/gif exigido.
- [ ] Preencher `04-test-report.md` com resultados, limitações e evidências.
- [ ] Revisar se os arquivos alterados são exatamente os da tabela acima.

**Timeline:** 0,5 dia.

**Total estimado:** 4–4,5 dias. Ajustar antes da Fase 1 se houver prazo externo.

### Riscos e mitigação

| Risco | Como perceber | Mitigação |
|---|---|---|
| Matcher não reproduz as 6 | `tests/test_api.py` falha em 199/296/4/5/7/3 | usar o predicado validado em `research/scripts/validar_sequencias.py`; comparar conjuntos |
| Ordem de páginas instável | páginas diferentes entre execuções | comparar conjuntos, não listas; usar `PYTHONHASHSEED=0` nos testes |
| Banco some no Docker | catálogo vazio após `rm` + novo `run` | `VOLUME`/`-v` documentado; teste de persistência na Fase 4 |
| Volume sombreia o CSV | app não encontra `data/top/dataset_final.csv` | montar `/app/db`, nunca `/app/data` |
| Duplicata/variação de acorde | dois cartões equivalentes | `normalized_key` única e `409`; normalização só lowercase |
| Busca lenta | tempo alto com 67k músicas | medir na Fase 1; manter o padrão de varredura atual; índice fica para o futuro |
| UI mostra só 100 | 199/296 truncados | limitação conhecida; não paginar nesta fase |
| Imagem com banco local | banco de dev aparece no container | `.dockerignore` com `db/` e `*.db` |

## Estratégia de Testes

### Testes Unitários

- `matching.py`: contíguo, ordem, repetição, acordes extras, case-insensitive,
  sequência vazia e sequência maior que a música.
- `db.py`: `init_db` idempotente, seed das 6, `normalized_key`, `criar`,
  `listar`, `buscar`, duplicata e banco temporário.
- `main.py`: `get_pagina` (página 1, 2, além do fim) e resolução de alias legado.

### Testes de Integração

- Flask test client + banco temporário (`DECIFRAME_DB`): `GET /sequencias`
  contém as 6; `POST` cria; `409` em duplicata; `400` em payload inválido.
- `/similares?sequencia=<id>` e alias legado para as 6: percorrer `pagina` até
  vazio, unir `id_unico_musica` e comparar com os golden sets
  (199/296/4/5/7/3; total 514); 0 duplicatas e 0 faltantes.
- Formato: 9 chaves por resultado, ausência de `diferenca`, 100 por página,
  `Content-Type: text/html` e corpo JSON.
- Persistência: criar, reiniciar o processo e reler; Docker `stop`/`start` e
  `rm` + novo `run` com o mesmo volume.
- **Frontend:** não há runner JS no repositório; a validação é manual e
  roteirizada (catálogo, cadastro, duplicata, busca, 6 originais, limite de 100,
  mobile). Automação E2E com Playwright/Karma fica fora do escopo desta fase
  para não introduzir um toolchain novo.

### Definição de Pronto

- [ ] `GET /sequencias` devolve as 6 originais em banco novo.
- [ ] `POST /sequencias` cadastra uma sequência nova e ela aparece no catálogo.
- [ ] `POST` duplicado devolve `409` com o `id` existente.
- [ ] `/similares` por `id` e pelo alias legado devolve os mesmos conjuntos das
  6: 199/296/4/5/7/3 (total 514), em todas as páginas.
- [ ] A página `#/porsequencia` carrega o catálogo, cadastra, busca e mostra
  resultados; as 6 continuam funcionando.
- [ ] O catálogo persiste após `docker stop`/`start` e após `rm` + novo `run`
  com o mesmo volume; sem volume, a perda é a esperada.
- [ ] `README.md`, `AGENTS.md` e ADR 0002 refletem o volume e o SQLite.
- [ ] `python3 -m unittest discover tests` passa; o relatório de testes está
  preenchido.

## Observabilidade

Não se aplica ao escopo atual: o app não tem logging estruturado, métricas ou
alertas, e esta mudança não introduz nenhum. A única exigência é **fail fast**:
se `init_db()` não conseguir criar/abrir o banco, o startup deve abortar com uma
exceção clara, em vez de servir com o catálogo silenciosamente vazio.

## Considerações Futuras

### Melhorias Potenciais

- Índice invertido/cache para o matcher, se o tempo de varredura incomodar.
- Normalização de grafias de acordes (sufixos/enarmônicos) com migração e
  revalidação dos 6 golden sets.
- Paginação de catálogo e de resultados; hoje a UI mostra no máximo 100.
- Autocomplete/chord builder e edição/exclusão de sequências.
- Migrations versionadas, backup e teste de concorrência com mais workers.
- Corrigir a constante `GENEROS` (51 vs 52; `R&B;`).

### Limitações Conhecidas

- Busca O(67k × tamanho da sequência), sem índice.
- Ordem de páginas dependente de `PYTHONHASHSEED`; o contrato observável é o
  conjunto.
- Sem normalização além de lowercase; variantes continuam sequências distintas.
- Catálogo aberto e anônimo, sem rate limiting/moderação.
- SQLite com 1 worker; se o número de workers aumentar, avaliar WAL e
  `busy_timeout`.
- Sem migrations/backup; apenas `CREATE TABLE IF NOT EXISTS` e seed idempotente.
- UI sem paginação e com a constante `GENEROS` desatualizada.

## Dependências

### Runtime

- Python 3.9, Flask 3.1.3, gunicorn 23.0.0 (já em `requirements.txt`).
- Stdlib: `sqlite3`, `json`, `os`, `unittest`. Nenhuma dependência nova.

### Dependências de Desenvolvimento

- Nenhuma nova. Testes com `unittest` da stdlib; Docker para o teste de
  persistência. E2E automatizado não faz parte desta fase.

## Considerações de Segurança

- **SQL injection:** todas as queries usam parâmetros (`?`), nunca interpolação
  de string.
- **Entrada:** validar `acordes` como lista de strings não vazias, com limites
  de 20 acordes e 20 caracteres por acorde; rejeitar payload malformado com
  `400`.
- **XSS:** os acordes são exibidos por interpolação AngularJS (`{{ }}`) e pela
  diretiva `df-hex`; não usar `ng-bind-html` para conteúdo do catálogo.
- **Acesso:** o catálogo é aberto e anônimo por requisito; autenticação, rate
  limiting, moderação e CSRF não se aplicam a esta fase (sem sessão/login).
- **Dados:** o banco contém apenas sequências de acordes públicas; não há dados
  pessoais.

## Estratégia de Rollout

1. **Desenvolvimento:** rodar com virtualenv e `DECIFRAME_DB=./db/sequences.db`
   (ou o default `db/sequences.db`); validar catálogo, cadastro e busca.
2. **Testes:** suíte unitária/integração, golden sets e teste de persistência
   com Docker.
3. **Deploy local:** `docker build -t ciframe .` e
   `docker run -p 8080:8080 -v ciframe-db:/app/db ciframe`; verificar
   `curl http://localhost:8080/generos` e o fluxo da página.
4. **Staging/produção:** não se aplica; o deploy é local-only por ADR 0001.
5. **Monitoramento:** smoke test manual após o deploy; sem métricas nesta fase.

## Referências

- `docs/features/sequencias-customizadas/00-enunciado.md`
- `docs/features/sequencias-customizadas/01-research.md`
- `docs/features/sequencias-customizadas/02-proposal.md`
- `research/01-matching-semantica.md`
- `research/02-validacao-hipotese.md`
- `research/03-banco-de-dados.md`
- `research/04-frontend-porsequencia.md`
- `research/scripts/validar_sequencias.py`
- `docs/adr/0001-local-only-docker-deploy.md`
- `docs/adr/0002-persist-custom-sequences.md`
- `scripts/generate_data_set.py:7-24`
