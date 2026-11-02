# Pesquisa 2 — Validação da hipótese contra os dados reais

> Documento descritivo do código em `fb97001` (2026-10-17). Não contém proposta,
> avaliação ou trabalho futuro. As referências usam `caminho/arquivo.ext:linha`.

## Escopo e método

Pergunta respondida: a pergunta 2 de
`docs/features/sequencias-customizadas/01-research.md:16-20` — rodar o algoritmo
candidato contra `data/top/dataset_final.csv`, para as 6 sequências hardcoded, e
confirmar ou refutar que ele reproduz os mesmos matches que o código atual produz
via `seqs_famosas`.

Como a pergunta 1 não fixa um algoritmo novo, foram testadas duas hipóteses que
descrevem o comportamento atual:

- **H1** — `get_famosas` (`scripts/generate_data_set.py:7-24`), reimplementado
  literalmente, reproduz o campo `SEQ_FAMOSA` do CSV.
- **H2** — o predicado “a sequência aparece como bloco contíguo (case-insensitive)
  **e** o vocabulário da música está contido no vocabulário da sequência”
  reproduz o mesmo conjunto, usando `musica.cifra` limpa por `limpa_cifra`
  (`main.py:11-23`).

Também foram medidas interpretações mais frouxas, para mostrar o que **não**
reproduz a tag: contígua sozinha, subsequência ordenada, apenas subconjunto de
vocabulário e qualquer interseção de acordes.

O script reproduzível é `research/scripts/validar_sequencias.py`. Ele:

1. lê o CSV com o mesmo parsing de `main.py:49-98` (descarta a primeira linha,
   aplica `replace('"','').replace('NA','')`, separa por `,`, faz
   `split(';')` na cifra e em `SEQ_FAMOSA`);
2. aplica `limpa_cifra` (`main.py:11-23`) à cifra;
3. reimplementa `get_famosas` literalmente;
4. compara **conjuntos de `id_unico_musica`**, música a música, com `assert`;
5. imprime as contagens por interpretação.

## Sumário

A hipótese H1 foi **confirmada**: `get_famosas` reproduz exatamente as 6 tags, com
199, 296, 4, 5, 7 e 3 músicas (total 514), sem nenhuma diferença de conjunto. A
hipótese H2 também foi **confirmada**: “bloco contíguo case-insensitive **e**
vocabulário da música ⊆ vocabulário da sequência” produz exatamente os mesmos
conjuntos das 6 tags, música a música. As interpretações mais frouxas foram
**refutadas** como descrição do comportamento atual: contígua sozinha devolve
866/1.216/3.110/96/1.039/132; subsequência ordenada devolve
4.763/5.887/13.643/427/3.641/280; apenas subconjunto devolve
9.014/9.099/8.165/8.194/8.159/8.198; qualquer interseção devolve
45.526/40.495/33.845/33.691/19.608/31.752. O endpoint real devolve exatamente os
conjuntos de H1/H2 (199/296/4/5/7/3), mas a **ordem** das páginas varia com o
`PYTHONHASHSEED`; o baseline de teste observável é o conjunto por sequência, não
a ordem nem o conteúdo de uma página específica.

## 1. Definições usadas no teste

| Termo | Definição no script |
|---|---|
| `contígua` | existe `i` tal que `cifra[i:i+n] == sequência`, com ambos lowercased; `n = len(sequência)` |
| `subseq. ordenada` | a sequência aparece na ordem, mas não necessariamente em posições consecutivas; acordes extras são permitidos |
| `subconjunto` | `set(cifra) ⊆ set(sequência)`: a música só usa acordes do vocabulário da sequência, em qualquer ordem/repetição |
| `interseção` | `set(cifra) ∩ set(sequência) ≠ ∅`: pelo menos um acorde em comum |
| `mesmo_vocab` | `set(cifra) == set(sequência)` |
| `tag` | `str(id_seq) in musica.seqs_famosas` (`main.py:209`), com `id_seq` 0–5 |

`cifra` é sempre a lista limpa por `limpa_cifra` (`main.py:11-23`), não a string
bruta. O `get_famosas` é aplicado à string bruta do CSV (`';'.join(raw)`), que é
o insumo do gerador; o `assert` de H1 confirma que esse insumo, depois do
parsing, ainda reproduz a tag.

## 2. Resultados de H1 e H2

Saída de `PYTHONHASHSEED=0 python3 research/scripts/validar_sequencias.py`:

```
linhas carregadas (main.py descarta a 1a): 67585
músicas com tag não vazia: 514
distribuição das tags: [((), 67071), (('1',), 296), (('0',), 199), (('4',), 7), (('3',), 5), (('2',), 4), (('5',), 3)]

seq | tag | get_famosas | igual? | contígua | subseq | subconj | intersec | mesmo_vocab | mesmo_vocab_sem_tag | contígua_sem_tag
----------------------------------------------------------------------------------------------------------------------------------
BmGDA | 199 | 199 | SIM | 866 | 4763 | 9014 | 45526 | 395 | 196 | 667
CGAmF | 296 | 296 | SIM | 1216 | 5887 | 9099 | 40495 | 532 | 236 | 920
EmG | 4 | 4 | SIM | 3110 | 13643 | 8165 | 33845 | 4 | 0 | 3106
CA7DmG7 | 5 | 5 | SIM | 96 | 427 | 8194 | 33691 | 6 | 1 | 91
GmF | 7 | 7 | SIM | 1039 | 3641 | 8159 | 19608 | 7 | 0 | 1032
CC7FFm | 3 | 3 | SIM | 132 | 280 | 8198 | 31752 | 3 | 0 | 129

total de músicas marcadas (soma das 6): 514
páginas de 100 necessárias: {'BmGDA': 2, 'CGAmF': 3, 'EmG': 1, 'CA7DmG7': 1, 'GmF': 1, 'CC7FFm': 1}
```

O script tem três `assert`s por sequência:

```python
assert tagged == hist, 'get_famosas não reproduziu a tag para ' + key
assert tagged == (cont & subset), 'contígua & subconjunto não reproduziu a tag para ' + key
assert not (tagged - cont), 'tag fora de contígua para ' + key
```

Todos passaram para as 6 sequências. A comparação é de conjuntos de
`id_unico_musica`, não de contagens: uma diferença de um único ID falharia.

### 2.1 H1 — `get_famosas` literal

| Sequência | tag | `get_famosas` | diferença |
|---|---:|---:|---|
| `BmGDA` | 199 | 199 | 0 |
| `CGAmF` | 296 | 296 | 0 |
| `EmG` | 4 | 4 | 0 |
| `CA7DmG7` | 5 | 5 | 0 |
| `GmF` | 7 | 7 | 0 |
| `CC7FFm` | 3 | 3 | 0 |

**Confirmada.** O `get_famosas` reimplementado é idêntico ao campo do CSV para
todas as 6 sequências.

### 2.2 H2 — contígua ∧ subconjunto

| Sequência | tag | contígua ∧ subconjunto | diferença |
|---|---:|---:|---|
| `BmGDA` | 199 | 199 | 0 |
| `CGAmF` | 296 | 296 | 0 |
| `EmG` | 4 | 4 | 0 |
| `CA7DmG7` | 5 | 5 | 0 |
| `GmF` | 7 | 7 | 0 |
| `CC7FFm` | 3 | 3 | 0 |

**Confirmada.** O predicado sobre `musica.cifra` limpa reproduz exatamente a tag,
sem precisar do campo `SEQ_FAMOSA`.

## 3. Resultados das interpretações mais frouxas

### 3.1 Contígua sozinha

| Sequência | tag | contígua | contígua − tag | tag − contígua |
|---|---:|---:|---:|---:|
| `BmGDA` | 199 | 866 | 667 | 0 |
| `CGAmF` | 296 | 1.216 | 920 | 0 |
| `EmG` | 4 | 3.110 | 3.106 | 0 |
| `CA7DmG7` | 5 | 96 | 91 | 0 |
| `GmF` | 7 | 1.039 | 1.032 | 0 |
| `CC7FFm` | 3 | 132 | 129 | 0 |

Toda música com tag é contígua (a coluna `tag − contígua` é 0), mas há muitas
músicas contíguas sem tag: são músicas que contêm o bloco, mas usam acordes fora
do vocabulário da sequência. Exemplo de `BmGDA`: `Every Time You Go` tem
`G6;D9;B9;Bm;G;C;A;A6;...` e contém `Bm;G;D;A` em algum ponto, mas tem acordes
extras; por isso não recebe a tag. **Refutada como descrição suficiente.**

### 3.2 Subsequência ordenada (sem contiguidade)

| Sequência | tag | subseq. ordenada | subseq. − tag |
|---|---:|---:|---:|
| `BmGDA` | 199 | 4.763 | 4.564 |
| `CGAmF` | 296 | 5.887 | 5.591 |
| `EmG` | 4 | 13.643 | 13.639 |
| `CA7DmG7` | 5 | 427 | 422 |
| `GmF` | 7 | 3.641 | 3.634 |
| `CC7FFm` | 3 | 280 | 277 |

A ordem sozinha não basta: permitir acordes entre os da sequência aumenta muito o
conjunto. A contiguidade faz parte do que a tag captura. **Refutada.**

### 3.3 Apenas subconjunto de vocabulário

| Sequência | tag | só subconjunto | subconjunto − tag |
|---|---:|---:|---:|
| `BmGDA` | 199 | 9.014 | 8.815 |
| `CGAmF` | 296 | 9.099 | 8.803 |
| `EmG` | 4 | 8.165 | 8.161 |
| `CA7DmG7` | 5 | 8.194 | 8.189 |
| `GmF` | 7 | 8.159 | 8.152 |
| `CC7FFm` | 3 | 8.198 | 8.195 |

Usar só acordes da sequência, em qualquer ordem, é muito mais amplo que a tag.
A ordem/contiguidade é o que separa. **Refutada.**

### 3.4 Qualquer interseção

| Sequência | tag | qualquer interseção | interseção − tag |
|---|---:|---:|---:|
| `BmGDA` | 199 | 45.526 | 45.327 |
| `CGAmF` | 296 | 40.495 | 40.199 |
| `EmG` | 4 | 33.845 | 33.841 |
| `CA7DmG7` | 5 | 33.691 | 33.686 |
| `GmF` | 7 | 19.608 | 19.601 |
| `CC7FFm` | 3 | 31.752 | 31.749 |

É o critério do modo `acordes` (`main.py:240-245`), não o da tag. **Refutada**
como descrição do modo sequência.

## 4. O que “mesmo match” significa neste código

O endpoint de sequência devolve uma lista paginada (`main.py:196`,
`main.py:226-228`), e a ordem dos blocos de gênero depende do `PYTHONHASHSEED`
(ver `research/01-matching-semantica.md`, §6.1). Portanto:

- o **conjunto** de músicas por sequência é estável e é o que H1/H2 reproduzem:
  199, 296, 4, 5, 7 e 3 (total 514);
- a **ordem** e o conteúdo de uma página específica não são estáveis entre
  processos;
- o número de páginas é 2, 3, 1, 1, 1 e 1 (`TAM_PAGINA = 100`, `main.py:35`);
- cada item do modo sequência tem 9 chaves (`main.py:210-220`), sem `diferenca`
  nem `intersecao`.

O baseline observável para comparar implementações é, portanto, o conjunto de
`id_unico_musica` por sequência (e o total 514), não a lista ordenada de uma
página.

## 5. Confirmação contra o endpoint real

O container foi construído com o `Dockerfile` do repositório e exercitado em
`localhost:18080`. Somando todas as páginas de cada sequência:

| Sequência | Total devolvido | Páginas | Conjunto = tag? |
|---|---:|---:|---|
| `BmGDA` | 199 | 2 (100 + 99) | sim |
| `CGAmF` | 296 | 3 (100 + 100 + 96) | sim |
| `EmG` | 4 | 1 | sim |
| `CA7DmG7` | 5 | 1 | sim |
| `GmF` | 7 | 1 | sim |
| `CC7FFm` | 3 | 1 | sim |

Também foram observados:

- `?sequencia=bm,g,d,a` → `[]` (chave case-sensitive, `main.py:194`);
- `?sequencia=Bm,G,D,A` → 100 na página 1 (vírgulas removidas, `main.py:191`);
- `?sequencia=XYZ` e `?sequencia=` → `[]`;
- `Content-Type: text/html; charset=utf-8` (`json.dumps`, `main.py:197`);
- `/generos` → 52 gêneros.

## 6. Casos de fronteira medidos

Os casos abaixo são os que separam as interpretações e podem ser usados como
casos de teste descritivos do comportamento atual.

### 6.1 Contígua mas sem tag (acordes extras)

| Sequência | Exemplo | Cifra (início) | Tag |
|---|---|---|---|
| `BmGDA` | `Every Time You Go` | `G6;D9;B9;Bm;G;C;A;A6;...` | — |

As contagens de `contígua − tag` para as 6 sequências estão na §3.1
(667, 920, 3.106, 91, 1.032 e 129).

### 6.2 Mesmo vocabulário, ordem diferente, sem tag

| Sequência | Exemplo | Cifra (início) | Tag |
|---|---|---|---|
| `BmGDA` | `Do Or Die` | `D;G;Bm;A;D;G;Bm;A;...` | — |
| `CGAmF` | `What's Left` | `C;G;C;G;C;G;F;G;...` | — |
| `CA7DmG7` | `Samba da Vizinha` | `C;Dm;A7;Dm;G7;...` | — |

### 6.3 Repetição não impede a tag

| Sequência | Exemplo | Cifra | Tag |
|---|---|---|---|
| `GmF` | `Marajá` | `Gm;F;Gm;F` | `4` |

## 7. Reprodução

```bash
# a partir da raiz do repositório
PYTHONHASHSEED=0 python3 research/scripts/validar_sequencias.py

# endpoint real
docker build -t ciframe .
docker run -p 8080:8080 ciframe
for s in BmGDA CGAmF EmG CA7DmG7 GmF CC7FFm; do
  for p in 1 2 3; do
    curl -s "http://localhost:8080/similares?sequencia=$s&pagina=$p"
  done
done
```

## 8. Referências de código

| Assunto | Referência |
|---|---|
| `get_famosas` | `scripts/generate_data_set.py:7-24` |
| Atribuição de `famosas` | `scripts/generate_data_set.py:84-89` |
| `limpa_cifra` | `main.py:11-23` |
| Carregamento | `main.py:49-98` |
| `seqs_famosas` | `main.py:63`, `musica.py:18` |
| Teste da tag no endpoint | `main.py:208-209` |
| `/similares` | `main.py:170-201` |
| Modo sequência | `main.py:190-197` |
| Paginação | `main.py:226-228`, `main.py:35` |
| Dicionário de sequências | `main.py:40-45` |
| Script de validação | `research/scripts/validar_sequencias.py` |
| Script de ordem | `research/scripts/ordem_endpoint.py` |
