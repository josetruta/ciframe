# Research — deciframe (estado atual)

Documentação descritiva do código em `fb97001` (2026-10-17), respondendo às quatro
perguntas de `docs/features/sequencias-customizadas/01-research.md`. Não há
proposta, avaliação, recomendação ou trabalho futuro nestes documentos.

## Documentos

| Documento | Pergunta | Resposta curta |
|---|---|---|
| [`01-matching-semantica.md`](01-matching-semantica.md) | 1 — algoritmo de matching | Hoje o match é um lookup exato numa tag pré-computada (`SEQ_FAMOSA`); a tag equivale a “bloco contíguo case-insensitive **e** vocabulário da música ⊆ vocabulário da sequência”. Ordem importa; repetição não; não há normalização de acordes no runtime. |
| [`02-validacao-hipotese.md`](02-validacao-hipotese.md) | 2 — validação contra os dados | `get_famosas` reproduz exatamente as 6 tags (199/296/4/5/7/3; total 514), música a música. O predicado “contígua ∧ subconjunto” também. Interpretações mais frouxas (contígua sozinha, subsequência, só subconjunto, interseção) não reproduzem. |
| [`03-banco-de-dados.md`](03-banco-de-dados.md) | 3 — banco embarcado e persistência | Não há banco hoje. A imagem `python:3.9-slim` já tem `sqlite3` (módulo), `dbm`/`shelve` e JSON/CSV/pickle; não tem o CLI `sqlite3`. O `Dockerfile` não tem `VOLUME`; o `docker run` do README não tem `-v`; `stop`/`start` preserva a camada gravável, `rm` + novo `run` não. |
| [`04-frontend-porsequencia.md`](04-frontend-porsequencia.md) | 4 — página `#/porsequencia` | A página tem 4 sequências hardcoded (`Bm G D A`, `C G Am F`, `Gm F`, `C C7 F Fm`), sem cadastro, sem persistência e sem paginação; mostra no máximo a primeira página (100) e não tem as sequências `EmG`/`CA7DmG7` que o backend tem. |

## Sumário executivo

O backend atual não calcula matching de sequência em tempo real: `/similares?sequencia=`
remove as vírgulas, faz lookup exato num dicionário de 6 chaves
(`main.py:40-45`, `main.py:190-197`) e devolve as músicas cujo campo pré-computado
`seqs_famosas` contém o índice (`main.py:203-223`). Esse campo vem da coluna
`SEQ_FAMOSA` do CSV, gerada por `get_famosas`
(`scripts/generate_data_set.py:7-24`), cujo predicado efetivo é “a sequência
aparece como bloco contíguo de acordes, sem diferenciar maiúsculas de minúsculas,
e o vocabulário de acordes da música está contido no vocabulário da sequência”.
A validação contra o CSV confirma que `get_famosas` e o predicado “contígua ∧
subconjunto” reproduzem exatamente as 6 tags (199, 296, 4, 5, 7 e 3 músicas;
total 514), enquanto interpretações mais frouxas produzem de 4× a 777× mais
resultados. Não há banco de dados: o CSV é lido uma vez no import e mantido em
memória; a imagem `python:3.9-slim` já contém o módulo `sqlite3`, `dbm`/`shelve`, mas o
`Dockerfile` não declara `VOLUME` e o `docker run` do README não monta nada, então
a camada gravável só sobrevive a `stop`/`start` do mesmo container. No frontend,
`#/porsequencia` tem 4 cartões hardcoded (faltam `EmG` e `CA7DmG7`), não tem
formulário de cadastro, não persiste nada e não pagina: envia a busca sem
`pagina` e exibe no máximo 100 resultados.

## Números-chave

| Sequência | Índice | Músicas com a tag | Páginas de 100 |
|---|---:|---:|---:|
| `BmGDA` | 0 | 199 | 2 |
| `CGAmF` | 1 | 296 | 3 |
| `EmG` | 2 | 4 | 1 |
| `CA7DmG7` | 3 | 5 | 1 |
| `GmF` | 4 | 7 | 1 |
| `CC7FFm` | 5 | 3 | 1 |
| **Total** | | **514** | |

Dados: 67.586 linhas no CSV; 67.585 carregadas (a primeira é descartada por
`main.py:50`); 59.444 com cifra; 8.141 sem cifra; 6.653 tokens de acorde
distintos; 52 gêneros; 303 linhas com `R&B;`.

## Método

- Leitura integral de `main.py`, `musica.py`, `scripts/generate_data_set.py`,
  `scripts/cifra_parser.py`, `scripts/normalize_chords.R`,
  `scripts/simplify_chords.R`, `scripts/build-chords-transitions.R`,
  `data/top/merge_datasets.R`, `README.md`, `AGENTS.md`, `CONTRIB.md`, dos três
  ADRs, dos cinco arquivos de
  `docs/features/sequencias-customizadas/`, do frontend envolvido
  (`index.html`, `app.js`, `routes.js`, controllers, templates, diretiva
  `df-hex`, CSS) e de `data/mapeamento_sequencias_famosas.txt`.
- Scripts reproduzíveis em [`scripts/`](scripts/), todos com a biblioteca padrão
  do Python 3.9:
  - `validar_sequencias.py` — parsing do CSV + `get_famosas` + predicados +
    `assert`s por música;
  - `medicoes_dados.py` — contagens de linhas, cifras, tokens, colisões,
    repetições, tablatura e títulos alterados por `replace('NA','')`;
  - `ordem_endpoint.py` — demonstra a dependência de ordem em relação ao
    `PYTHONHASHSEED`.
- Ambiente de execução: Python 3.9.12 no host; Docker 28.3.2; imagem
  `python:3.9-slim` com Python 3.9.25 e SQLite 3.46.1; gunicorn 23.0.0.
- A API foi exercitada contra um container construído com o `Dockerfile` do
  repositório, em `localhost:18080`.

## Reprodução

```bash
# a partir da raiz do repositório
PYTHONHASHSEED=0 python3 research/scripts/validar_sequencias.py
PYTHONHASHSEED=0 python3 research/scripts/medicoes_dados.py
PYTHONHASHSEED=0 python3 research/scripts/ordem_endpoint.py
PYTHONHASHSEED=1 python3 research/scripts/ordem_endpoint.py

# API real
docker build -t ciframe .
docker run -p 8080:8080 ciframe
curl 'http://localhost:8080/similares?sequencia=BmGDA'
curl 'http://localhost:8080/similares?sequencia=bm,g,d,a'
curl 'http://localhost:8080/generos'
```

## Observações de leitura

- As referências de código usam `caminho/arquivo.ext:linha` ou
  `caminho/arquivo.ext:linha-inicial-linha-final`.
- Os documentos descrevem o código como ele está; não há juízo sobre o que é
  “melhor” nem sugestão de mudança.
- O diretório `research/` é o único artefato não versionado no momento da
  pesquisa (`git status`); `docs/features/sequencias-customizadas/01-research.md`
  tem uma modificação local (o registro das descobertas) e o restante do
  repositório está em `fb97001`.
