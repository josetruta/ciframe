# Plano — Sequências de Acordes Customizadas

## Passos

1. [ ] Extrair `contigua`, `vocabulario_contido` e `musica_casa_sequencia` para
   `matching.py`. A música casa quando a sequência aparece como bloco contíguo
   case-insensitive e `set(musica.cifra) ⊆ set(sequencia)`. Somente lowercase;
   sem normalização de sufixos ou enarmônicos.
2. [ ] Criar `tests/test_matching.py`: bloco contíguo, ordem diferente, repetição
   na música, acorde extra, case-insensitive, sequência vazia, sequência maior
   que a música e repetição na sequência.
3. [ ] Criar `db.py` com `DB_PATH` configurável (`DECIFRAME_DB`, default
   `db/sequences.db`), `init_db`, `listar_sequencias`, `criar_sequencia`,
   `buscar_sequencia` e `buscar_por_alias_legado`.
4. [ ] Schema `sequences` (`id`, `chords_json`, `normalized_key` única,
   `created_at`) e seed idempotente das 6: `Bm,G,D,A`, `C,G,Am,F`, `Em,G`,
   `C,A7,Dm,G7`, `Gm,F`, `C,C7,F,Fm`. `criar_sequencia` de duplicata levanta
   erro. Cobrir em `tests/test_db.py` com banco temporário.
5. [ ] Em `main.py`, chamar `init_db()` no startup e manter o CSV em memória.
   Adicionar `GET /sequencias` e `POST /sequencias`, sempre com `json.dumps`.
   `POST` recebe `{"acordes": [...]}`: lista não vazia, até 20 acordes, 1–20
   caracteres cada; `201` criado, `400` inválido, `409` duplicata com o `id`
   existente.
6. [ ] Adaptar `/similares`: `sequencia` numérica resolve por `id`; senão, alias
   legado das 6 (`BmGDA` ou `Bm,G,D,A`). Inexistente devolve `[]`. Substituir o
   teste da tag por `matching.musica_casa_sequencia(musica.cifra, acordes_seq)`.
   Manter `generos`, `pagina` e 100 por página. Resultados com as 9 chaves
   atuais, sem `diferenca`.
7. [ ] Criar `tests/test_api.py`: catálogo inicial, criação, duplicata, payload
   inválido, 9 chaves, `Content-Type: text/html`, paginação de 100, alias
   legado, sequência customizada, filtro de gênero, sequência inexistente e os
   golden sets 199/296/4/5/7/3 (total 514), percorrendo todas as páginas e
   comparando conjuntos.
8. [ ] Em `sequencia.js`, remover `sequencia1`..`sequencia4`. Carregar
   `GET /sequencias`, mapear cada acorde para `{acorde, cor: '#2E1C74'}` e
   buscar com `similares?sequencia=<id>`. Formulário de texto `Bm, G, D, A`:
   dividir por vírgula/espaço, `POST /sequencias`, recarregar e selecionar a
   nova; em `409`, selecionar a existente.
9. [ ] Em `sequencia.html`, trocar o `ng-repeat` de `sequenciasFamosas` pelo
   catálogo da API e adicionar o formulário inline. Manter o bloco selecionado,
   os resultados e `routes.js`. Sem chips, autocomplete, rota nova ou paginação.
10. [ ] `Dockerfile`: `RUN mkdir -p /app/db` e `VOLUME ["/app/db"]`. Excluir
    `db/` e `*.db` no `.dockerignore` e ignorar `db/` no `.gitignore`. Documentar
    `docker run -p 8080:8080 -v ciframe-db:/app/db ciframe` no `README.md` e no
    `AGENTS.md`. Registrar SQLite + volume em
    `docs/adr/0002-persist-custom-sequences.md`.
11. [ ] Verificar persistência: banco novo semeia as 6; criação sobrevive a
    `docker stop`/`start` e a `docker rm` + novo `run` com o mesmo volume; sem
    `-v`, o `rm` volta às 6. Rodar a suíte e preencher o relatório de testes.

## Arquivos afetados

| Arquivo | Mudança |
|---|---|
| `main.py` | `init_db`, `GET`/`POST /sequencias`, resolução de `id`/alias em `/similares`, matcher no lugar da tag |
| `musica.py` | sem mudança; `cifra` e `acordes` já existem |
| `static/assets/js/controllers/sequencia.js` | catálogo via API, formulário/criação, busca por `id` |
| `static/templates/sequencia.html` | cartões dinâmicos e formulário inline |
| `matching.py` | predicado contíguo e subconjunto, case-insensitive |
| `db.py` | schema `sequences`, seed, CRUD e conexão SQLite |
| `Dockerfile` | `RUN mkdir -p /app/db` e `VOLUME ["/app/db"]` |
| `.dockerignore` | excluir `db/` e `*.db` |
| `.gitignore` | ignorar `db/` local |
| `README.md` | SQLite e `docker run` com `-v ciframe-db:/app/db` |
| `AGENTS.md` | comando Docker com volume e gotcha do catálogo persistido |
| `tests/test_matching.py` | unidade do matcher |
| `tests/test_db.py` | schema, seed, CRUD e duplicata |
| `tests/test_api.py` | contrato, golden sets, paginação e alias legado |
| `docs/adr/0002-persist-custom-sequences.md` | decisão SQLite + volume |

`scripts/generate_data_set.py`, `static/assets/js/app.js`, `routes.js`,
`index.html`, `requirements.txt` e `data/top/*.csv` ficam intactos.

## Riscos e mitigação

| Risco | Como perceber | Mitigação |
|---|---|---|
| Matcher não reproduz as 6 | `tests/test_api.py` falha em 199/296/4/5/7/3 | usar o predicado já validado; comparar conjuntos |
| Ordem de páginas instável | páginas diferentes entre execuções | comparar conjuntos, não listas; `PYTHONHASHSEED=0` nos testes |
| Banco some no Docker | catálogo vazio após `rm` + novo `run` | `VOLUME` e `-v` documentados; teste de persistência |
| Volume sombreia o CSV | app não encontra `data/top/dataset_final.csv` | montar `/app/db`, nunca `/app/data` |
| Duplicata ou variação de acorde | dois cartões equivalentes | `normalized_key` única e `409`; normalização só lowercase |
| Busca lenta | tempo alto com 67.585 músicas | medir a varredura; índice fica para o futuro |
| UI mostra só 100 | 199 e 296 truncados | limitação conhecida; não paginar nesta fase |
| Imagem com banco local | banco de dev aparece no container | `.dockerignore` com `db/` e `*.db` |

## Definição de pronto

- [ ] `GET /sequencias` devolve as 6 originais em banco novo.
- [ ] `POST /sequencias` cadastra uma sequência nova e ela aparece no catálogo.
- [ ] `POST` duplicado devolve `409` com o `id` existente.
- [ ] `/similares` por `id` e pelo alias legado devolve os mesmos conjuntos das
  6: 199, 296, 4, 5, 7 e 3 (total 514), em todas as páginas.
- [ ] A página `#/porsequencia` carrega o catálogo, cadastra, busca e mostra
  resultados; as 6 continuam funcionando.
- [ ] O catálogo persiste após `docker stop`/`start` e após `rm` + novo `run`
  com o mesmo volume; sem volume, a perda é a esperada.
- [ ] `README.md`, `AGENTS.md` e a ADR 0002 refletem o volume e o SQLite.
- [ ] `python3 -m unittest discover tests` passa e o relatório de testes está
  preenchido.
