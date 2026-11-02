# Relatório de testes — Sequências de Acordes Customizadas

## Cobertura

A suíte usa `unittest` da stdlib e roda contra o CSV real
(`data/top/dataset_final.csv`) para os golden sets. O banco de cada teste é um
arquivo temporário; nenhum teste escreve no banco de desenvolvimento.

- `tests/test_matching.py` — 9 testes: bloco contíguo, ordem diferente,
  repetição na música, acorde extra na música, case-insensitive, sequência
  vazia, sequência maior que a música, vocabulário contido e repetição na
  sequência.
- `tests/test_db.py` — 8 testes: seed das 6, `init_db` idempotente, criação,
  busca por id, duplicata exata, duplicata normalizada (lowercase) e alias
  legado (incluindo todas as 6 chaves).
- `tests/test_api.py` — 11 testes: catálogo inicial, criação (`201`), duplicata
  (`409`), payload inválido (`400`), formato de 9 chaves e
  `Content-Type: text/html`, paginação de 100, alias legado (`BmGDA` e
  `Bm,G,D,A`), sequência customizada, filtro de gênero e sequência inexistente.

Resultado: **28 testes, 0 falhas**, em **16,619 s**.

Fora da suíte, o app foi iniciado com `DECIFRAME_DB` temporário:

- `GET /sequencias` → `200`, 6 sequências semeadas, `text/html`.
- `POST /sequencias` com `D,A,Bm,G` → `201`, `{"id": 7, ...}`.
- `POST` repetido de `Bm,G,D,A` → `409`, `{"erro": "sequencia ja existe", "id": 1}`.
- `GET /similares?sequencia=7` → `200`, resultados no formato antigo.
- `GET /similares?sequencia=BmGDA` → `200`, primeira página com 100.
- `GET /similares?sequencia=9999` → `200`, `[]`.
- `GET /generos` → `200`, 52 gêneros.

O `Dockerfile` foi construído com volume nomeado: banco novo tem 6 sequências;
após criação, 7; `docker stop` + `docker start` mantém 7; `docker rm` + novo
`docker run` com o mesmo volume mantém 7; sem `-v`, o `rm` volta a 6.

Uma varredura do CSV completo (67.585 músicas) levou 0,486 s, 0,492 s, 0,482 s,
0,494 s, 0,478 s e 0,488 s para as 6 sequências, total 2,918 s.

## Teste de regressão obrigatório

As 6 sequências originais (`main.py`, linhas 40-45) precisam continuar
retornando os mesmos resultados de antes da migração para o banco de dados.

Elas saíram do dicionário fixo e passaram a ser o seed de `db.py`
(`SEQUENCIAS_ORIGINAIS`). O teste `test_golden_sets` percorre todas as páginas
de `/similares?sequencia=<id>` e compara o conjunto de `id_unico_musica` com o
conjunto calculado a partir da tag `seqs_famosas` do CSV, que permanece como
oráculo de regressão.

| Sequência | Músicas | Duplicatas | Faltantes |
|---|---:|---:|---:|
| `Bm,G,D,A` | 199 | 0 | 0 |
| `C,G,Am,F` | 296 | 0 | 0 |
| `Em,G` | 4 | 0 | 0 |
| `C,A7,Dm,G7` | 5 | 0 | 0 |
| `Gm,F` | 7 | 0 | 0 |
| `C,C7,F,Fm` | 3 | 0 | 0 |
| **Total** | **514** | **0** | **0** |

O alias legado (`?sequencia=BmGDA` e `?sequencia=Bm,G,D,A`) devolve o mesmo
conjunto do `id` semeado. O formato permanece: 9 chaves, sem `diferenca`, 100
por página e `Content-Type: text/html; charset=utf-8`.

## Como rodar

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
PYTHONHASHSEED=0 python -m unittest discover -s tests -v
```

O `PYTHONHASHSEED=0` não é necessário para a asserção (os testes comparam
conjuntos), mas deixa a ordem das páginas reproduzível.

## O que ficou de fora

- **E2E automatizado:** não há runner JS no repositório; Playwright/Karma não
  foram adicionados. A página foi prevista como verificação manual.
- **Concorrência:** SQLite foi testado com o gunicorn em 1 worker. WAL,
  `busy_timeout` e múltiplos workers não foram exercitados.
- **Migrations/backup:** apenas `CREATE TABLE IF NOT EXISTS` e seed idempotente;
  não há versionamento de schema nem backup.
- **Normalização:** somente lowercase; variantes de grafia e enarmônicos
  continuam sendo sequências distintas.
- **Paginação da UI:** a página continua mostrando no máximo 100 resultados;
  `Bm,G,D,A` (199) e `C,G,Am,F` (296) ficam truncados na interface, como antes.
- **`GENEROS`:** a constante JS continua com 51 gêneros; `/generos` retorna 52
  (falta `R&B;`).
- **Rate limiting, moderação e autenticação:** o catálogo é anônimo e aberto;
  esses controles não foram implementados.
