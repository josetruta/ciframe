# Pesquisa — Sequências de Acordes Customizadas

Fontes: `research/01-matching-semantica.md`, `research/02-validacao-hipotese.md`,
`research/03-banco-de-dados.md`, `research/04-frontend-porsequencia.md`.

## Perguntas que você precisa responder

1. **Algoritmo de matching**: hoje, as 6 sequências hardcoded em `main.py` (linhas
   40-45) são comparadas contra músicas via uma tag pré-computada
   (`SEQ_FAMOSA`/`seqs_famosas`, vinda do CSV). Sequências cadastradas pelo usuário
   não têm essa tag — o matching precisa ser calculado em tempo real a partir da
   lista de acordes de cada música (`musica.acordes`/`musica.cifra`). O que vai
   definir "a sequência X aparece na música Y"? A ordem dos acordes importa?
   Repetições de acorde dentro da música importam? É preciso normalizar (ex.:
   maiúsculas/minúsculas, variações de escrita do mesmo acorde)?
2. **Validação da hipótese**: rode o algoritmo que você está considerando contra os
   dados reais em `data/top/dataset_final.csv`, para as 6 sequências hoje
   hardcoded, e confirme (ou refute) que ele reproduz os mesmos matches que o
   código atual produz via `seqs_famosas`. Esse é o bar mínimo de correção que
   você vai usar na fase de testes.
3. **Banco de dados**: quais bancos embarcados (sem serviço externo adicional) são
   viáveis dentro do container Docker único e local-only já documentado em
   `docs/adr/0001-local-only-docker-deploy.md`? O que cada opção implica para o
   `Dockerfile` atual e para a persistência dos dados entre reinícios do
   container?
4. **Frontend existente**: o que a página `#/porsequencia`
   (`static/templates/sequencia.html` +
   `static/assets/js/controllers/sequencia.js`) já faz? Repare que ela tem hoje uma
   lista *hardcoded no JavaScript* de 4 sequências (`sequencia1`..`sequencia4`),
   diferente das 6 que existem no backend — um detalhe real e pré-existente do
   código, não um erro seu, que vale entender antes de decidir o que precisa
   mudar.

## Registro das descobertas

1. **Matching.** Hoje o match não é calculado em tempo real: `/similares?sequencia=`
   tira as vírgulas, faz lookup exato num dicionário de 6 chaves (`main.py:40-45`,
   `main.py:190-197`) e devolve as músicas cujo `seqs_famosas` contém o índice
   (`main.py:203-223`). A tag vem de `get_famosas`
   (`scripts/generate_data_set.py:7-24`): bloco contíguo, sem diferenciar
   maiúsculas de minúsculas, e vocabulário da música ⊆ vocabulário da sequência.
   A ordem importa; repetição não. No runtime não há normalização de acordes
   (`limpa_cifra` só tira tablatura e espaços, `main.py:11-23`). O que existe para
   calcular ao vivo é `musica.cifra` (lista ordenada, com repetição) e
   `musica.acordes` (conjunto) (`musica.py:16-17`).

2. **Validação.** `get_famosas` e o predicado “contígua ∧ subconjunto” reproduzem
   exatamente as 6 tags, música a música: 199, 296, 4, 5, 7 e 3 (total 514).
   Contígua sozinha, subsequência ordenada, só subconjunto e qualquer interseção
   não reproduzem. O endpoint devolve os mesmos conjuntos; a ordem das páginas
   varia com `PYTHONHASHSEED`. O baseline observável é o conjunto por sequência.

3. **Banco.** Não há banco: o CSV é lido uma vez no import (`main.py:49-98`). Na
   imagem `python:3.9-slim` já estão o módulo `sqlite3` (SQLite 3.46.1, sem o
   binário `sqlite3`), `dbm`/`shelve` e JSON/CSV/pickle; nenhum é usado. O
   `Dockerfile` não tem `VOLUME` e o `docker run` do README não tem `-v`.
   `stop`/`start` do mesmo container preserva a camada gravável; `rm` + novo
   `run` não. PostgreSQL, MySQL, Redis e MongoDB exigem serviço externo.

4. **Frontend.** `#/porsequencia` tem 4 cartões hardcoded (`Bm G D A`, `C G Am F`,
   `Gm F`, `C C7 F Fm`); faltam `EmG` e `CA7DmG7`. Não há cadastro, persistência,
   sequência na URL nem paginação: a busca vai sem `pagina` e mostra no máximo a
   primeira página (100), reordenada no cliente por `-popularidade`. O seletor de
   gênero usa a constante `GENEROS` (51 itens), não `/generos` (52; falta `R&B;`).

## Trade-offs identificados

**Algoritmo.** “Contígua ∧ subconjunto” é o único predicado medido que reproduz as
6 tags. Contígua sozinha, subsequência, só subconjunto e interseção devolvem de
cerca de 4× a centenas de vezes mais músicas. A ordem da resposta não é estável
entre processos.

**Banco.** `sqlite3`, `dbm`/`shelve` e JSON/CSV/pickle não pedem dependência nova
nem mudança obrigatória no `Dockerfile`; o arquivo na camada gravável sobrevive a
`stop`/`start` e se perde em `rm`, salvo `VOLUME` ou `-v`. Memória (o estado
atual) não persiste entre reinícios do processo. Serviço externo pede driver,
segundo container, rede e volume próprio.
