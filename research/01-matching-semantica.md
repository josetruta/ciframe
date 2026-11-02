# Pesquisa 1 — O que define “a sequência X aparece na música Y” hoje

> Documento descritivo do código em `fb97001` (2026-10-17). Não contém proposta,
> avaliação ou trabalho futuro. As referências de código usam o formato
> `caminho/arquivo.ext:linha-inicial-linha-final`.

## Escopo e método

Pergunta respondida: a pergunta 1 de
`docs/features/sequencias-customizadas/01-research.md:8-15` — como as 6 sequências
hardcoded são comparadas com as músicas hoje, o que define o match, se ordem e
repetição importam e se há normalização.

Método:

- leitura integral de `main.py`, `musica.py`, `scripts/generate_data_set.py`,
  `scripts/cifra_parser.py`, `scripts/normalize_chords.R`,
  `scripts/simplify_chords.R`, `scripts/build-chords-transitions.R`,
  `data/top/merge_datasets.R` e do frontend envolvido;
- leitura integral de `data/top/dataset_final.csv` por script, com o mesmo
  parsing de `main.py:49-98`;
- reprodução literal de `get_famosas` e comparação, música a música, com o
  campo `SEQ_FAMOSA` do CSV;
- execução da API real em container Docker (`/generos`, `/similares`);
- medições reproduzíveis em `research/scripts/` (ver apêndice B).

## Sumário

Hoje o match de sequência **não é calculado em tempo real**: `/similares?sequencia=`
remove as vírgulas, faz um lookup exato num dicionário de 6 chaves
(`main.py:40-45`, `main.py:190-197`) e devolve as músicas cujo campo pré-computado
`seqs_famosas` contém o índice da sequência (`main.py:203-223`). Esse campo vem da
coluna `SEQ_FAMOSA` do CSV, gerada por `get_famosas`
(`scripts/generate_data_set.py:7-24`), cujo predicado efetivo é: **a sequência
aparece como um bloco contíguo de acordes, sem diferenciar maiúsculas de
minúsculas, e o vocabulário de acordes da música está contido no vocabulário da
sequência**. A ordem importa — o mesmo vocabulário em ordem diferente não recebe a
tag —, mas repetições não importam, porque a condição de vocabulário é sobre
conjunto e a tag é gerada sobre a string de acordes. Não há normalização de
acordes no runtime: `limpa_cifra` só remove tablatura/espaços
(`main.py:11-23`), `musica.acordes` é um `set` exato (`musica.py:17`) e o único
lowercase acontece no gerador da tag (`scripts/generate_data_set.py:12`). As
estruturas que existem para um cálculo em tempo real são `musica.cifra` (lista
ordenada, com repetição) e `musica.acordes` (conjunto, sem ordem nem repetição)
(`musica.py:16-17`).

## 1. O caminho de uma busca por sequência, ponta a ponta

### 1.1 Frontend

O controller monta a URL juntando os acordes com vírgula
(`static/assets/js/controllers/sequencia.js:55-61`) e faz
`GET similares?sequencia=Bm,G,D,A` (`static/assets/js/controllers/sequencia.js:72-77`).
O backend recebe a string com vírgulas.

### 1.2 Rota `/similares`

`main.py:170-201` trata três modos no mesmo endpoint:

| Parâmetro | Linhas | O que faz |
|---|---|---|
| `acordes` | `main.py:185-186` | `split(',')` e segue para `get_similares` |
| `id_unico_musica` | `main.py:187-189` | pega `musica.acordes` e segue para `get_similares` |
| `sequencia` | `main.py:190-197` | remove vírgulas, lookup no dicionário e retorna direto |

No modo sequência:

```python
# main.py:190-197
elif sequencia_tag:
    acordes = sequencia_tag.replace(',','')
    similares = []
    if acordes in sequencias:
        id_seq = sequencias[acordes]
        similares = get_pagina(get_similares_por_sequencia(id_seq, generos_key), pagina_tag)
    return json.dumps(similares)
```

O dicionário é fixo e tem 6 entradas (`main.py:40-45`):

| Chave | Índice | Sequência |
|---|---|---|
| `BmGDA` | 0 | Bm, G, D, A |
| `CGAmF` | 1 | C, G, Am, F |
| `EmG` | 2 | Em, G |
| `CA7DmG7` | 3 | C, A7, Dm, G7 |
| `GmF` | 4 | Gm, F |
| `CC7FFm` | 5 | C, C7, F, Fm |

Consequências observadas:

- a comparação da chave é **exata e case-sensitive**: `?sequencia=bm,g,d,a`
  devolve `[]` (medido no container; ver §6);
- a remoção de vírgulas é o único tratamento da string: `Bm,G,D,A` e `BmGDA`
  caem na mesma chave;
- chave desconhecida (`XYZ`) devolve `[]` (o `similares` fica vazio e é
  serializado em `main.py:197`).

### 1.3 `get_similares_por_sequencia`

`main.py:203-223`:

1. filtra a coleção por gênero com `apply_filtro(musicas.values(), generos_key)`
   (`main.py:205`);
2. percorre a coleção e testa `if str(id_seq) in musica.seqs_famosas`
   (`main.py:208-209`);
3. monta um dicionário de 9 chaves (`main.py:210-220`) e acrescenta em
   `similares` (`main.py:221`);
4. devolve a lista (`main.py:223`).

O dicionário devolvido tem `id_unico_musica`, `id_artista`, `id_musica`,
`nome_artista`, `nome_musica`, `popularidade`, `acordes`, `genero` e `url`
(`main.py:210-220`). Não tem `diferenca` nem `intersecao` — diferente do modo
`acordes` (`main.py:246-258`).

### 1.4 Filtro de gênero e paginação

- `generos_key` é a lista global `generos` (`main.py:180`) ou o resultado de
  `generos_tag.split(',')` (`main.py:181-182`).
- `apply_filtro` (`main.py:266-272`) concatena os blocos `genero_musicas[genero]`
  apenas para gêneros que existem em `generos` (`main.py:269-271`); gêneros
  desconhecidos são silenciosamente ignorados.
- `genero_musicas` é montado no carregamento (`main.py:82-85`) e ordenado por
  popularidade decrescente (`main.py:94-96`).
- `get_pagina` (`main.py:226-228`) fatia `(pagina-1)*100 : (pagina-1)*100+100`;
  `TAM_PAGINA = 100` (`main.py:35`); `pagina` default é `'1'` (`main.py:176`).
- A resposta é `json.dumps(...)` (`main.py:197`), não `jsonify`; o
  `Content-Type` observado é `text/html; charset=utf-8`.

## 2. De onde vem a tag `SEQ_FAMOSA`

### 2.1 Coluna do CSV

O CSV não tem cabeçalho. As colunas são definidas em `main.py:25-34`:

| Índice | Constante | Conteúdo |
|---|---|---|
| 0 | `ARTISTA_ID` | id do artista |
| 1 | `MUSICA_ID` | id da música |
| 2 | `ARTISTA` | nome do artista |
| 3 | `MUSICA` | nome da música |
| 4 | `GENERO` | gênero |
| 5 | `POPULARIDADE` | popularidade |
| 6 | `TOM` | tom |
| 7 | `SEQ_FAMOSA` | tag(s) de sequência |
| 8 | `CIFRA` | acordes separados por `;` |

No carregamento, `musica[SEQ_FAMOSA] = musica[SEQ_FAMOSA].split(";")`
(`main.py:63`) e o valor é passado para `Musica` (`main.py:69-72`), que guarda em
`self.seqs_famosas` (`musica.py:18`). Para uma música sem tag, o campo vira
`['']` (porque `''.split(';')` é `['']`); para uma música com a tag `0`, vira
`['0']`.

### 2.2 Gerador `get_famosas`

`scripts/generate_data_set.py:7-24`:

```python
def get_famosas(acorde):
    seqs = ['bm;g;d;a','c;g;am;f', 'em;g' , 'c;a7;dm;g7', 'gm;f', 'c;c7;f;fm' ]
    out = []
    for i in range(len(seqs)):
        s = seqs[i]
        acorde = acorde.lower()
        if s in acorde:
            achou = True
            tem_seqs = []
            for l in acorde.split(';'):
                tokens = s.split(';')
                if l not in tokens:
                    achou = False
                    break
            if achou:
                tem_seqs.append(str(i))
                out.append("-".join(tem_seqs))
    return out
```

O predicado tem duas partes:

1. `s in acorde` (`scripts/generate_data_set.py:13`): a sequência, escrita com
   `;`, aparece como **substring** da string de acordes da música, depois de
   ambos serem lowercased (`scripts/generate_data_set.py:12`). Como a string é
   `acorde1;acorde2;...`, isso equivale a um bloco contíguo de acordes.
2. o laço `for l in acorde.split(';')` (`scripts/generate_data_set.py:16-20`):
   **todo** token da música precisa estar na lista de tokens da sequência
   (`if l not in tokens: achou = False`). Ou seja, o vocabulário da música está
   contido no vocabulário da sequência.

O índice é a posição na lista `seqs` (`scripts/generate_data_set.py:8`), que é a
mesma ordem de `main.py:40-45`. A lista `tem_seqs` tem no máximo um elemento
(`scripts/generate_data_set.py:22`), então o `"-".join(tem_seqs)` de
`scripts/generate_data_set.py:23` não insere separador na prática.

### 2.3 Atribuição no CSV

`scripts/generate_data_set.py:84-89`:

```python
famosas = 'NA'
famosas_list = get_famosas(str_notas)
if famosas_list:
    famosas = ''.join(get_famosas(str_notas))
print ','.join([artista,musica,nome_artista,nome_musica,nome_estilo,popularidade,tom,famosas,str_notas])
```

- `str_notas` é montada a partir dos `<b>` da cifra (`scripts/generate_data_set.py:70-74`),
  com `;` entre os acordes; se vazia, vira `'NA'` (`scripts/generate_data_set.py:75-76`).
- `famosas = ''.join(get_famosas(str_notas))` (`scripts/generate_data_set.py:88`)
  concatena os índices. Se uma música casasse com duas sequências, o campo viraria
  `'01'`, `'12'` etc. **Não existe nenhuma linha assim no CSV atual**: a
  distribuição medida é 67.071 músicas sem tag, 296 com `1`, 199 com `0`, 7 com
  `4`, 5 com `3`, 4 com `2` e 3 com `5` (total 514 com tag; ver apêndice A).
  Se existisse `'01'`, o teste `str(id_seq) in musica.seqs_famosas`
  (`main.py:209`) não casaria nem `'0'` nem `'1'`, porque a lista seria `['01']`.
- O arquivo `data/mapeamento_sequencias_famosas.txt` lista os rótulos dos índices
  0–5, mas **não é lido por nenhum código** (grep no repositório); é só
  documentação auxiliar.

## 3. O que a tag significa na prática

### 3.1 Predicado efetivo

A tag atual é reproduzida, música a música, por:

```
contígua(cifra_limpa, sequência, case-insensitive)
E
vocabulário(cifra_limpa) ⊆ vocabulário(sequência)
```

onde “contígua” é a existência de `len(sequência)` tokens consecutivos iguais à
sequência e “vocabulário” é o conjunto de tokens distintos.

A tabela abaixo é a saída de `research/scripts/validar_sequencias.py` (asserts
por música, não só por contagem):

| Sequência | tag | `get_famosas` | igual? | contígua | subconjunto | contígua ∧ subconjunto | igual à tag? |
|---|---:|---:|---|---:|---:|---:|---|
| `BmGDA` | 199 | 199 | SIM | 866 | 9.014 | 199 | SIM |
| `CGAmF` | 296 | 296 | SIM | 1.216 | 9.099 | 296 | SIM |
| `EmG` | 4 | 4 | SIM | 3.110 | 8.165 | 4 | SIM |
| `CA7DmG7` | 5 | 5 | SIM | 96 | 8.194 | 5 | SIM |
| `GmF` | 7 | 7 | SIM | 1.039 | 8.159 | 7 | SIM |
| `CC7FFm` | 3 | 3 | SIM | 132 | 8.198 | 3 | SIM |

“subconjunto” = vocabulário da música ⊆ vocabulário da sequência. O
`contígua ∧ subconjunto` é idêntico à tag nas 6 sequências (o script falha com
`AssertionError` se não for). O `get_famosas` reimplementado também é idêntico à
tag nas 6.

Para comparação, interpretações mais frouxas produzem muito mais músicas:

| Sequência | tag | contígua | subseq. ordenada | só subconjunto | qualquer interseção |
|---|---:|---:|---:|---:|---:|
| `BmGDA` | 199 | 866 | 4.763 | 9.014 | 45.526 |
| `CGAmF` | 296 | 1.216 | 5.887 | 9.099 | 40.495 |
| `EmG` | 4 | 3.110 | 13.643 | 8.165 | 33.845 |
| `CA7DmG7` | 5 | 96 | 427 | 8.194 | 33.691 |
| `GmF` | 7 | 1.039 | 3.641 | 8.159 | 19.608 |
| `CC7FFm` | 3 | 132 | 280 | 8.198 | 31.752 |

- “subseq. ordenada” = a sequência aparece na ordem, mas não necessariamente
  contígua, e acordes extras são permitidos.
- “só subconjunto” = a música só usa acordes do vocabulário da sequência, em
  qualquer ordem/repetição.
- “qualquer interseção” = a música tem pelo menos um acorde em comum com a
  sequência.

A conclusão descritiva é que a tag não é “contém a sequência em qualquer lugar”:
contígua sozinha devolve de 4,1× (`CGAmF`) a 777,5× (`EmG`) mais músicas; a
condição de vocabulário é o que reduz para o conjunto exato da tag.

### 3.2 Ordem

A ordem importa em duas camadas:

1. `s in acorde` (`scripts/generate_data_set.py:13`) é uma substring da string
   `;`-separada, portanto sensível à ordem.
2. `contígua` no script de validação também é sensível à ordem.

Evidência: músicas cujo vocabulário é exatamente o da sequência, mas em ordem
diferente, e que **não** recebem a tag (`mesmo_vocab_sem_tag`):

| Sequência | músicas com o vocabulário exato | sem tag (ordem diferente) |
|---|---:|---:|
| `BmGDA` | 395 | 196 |
| `CGAmF` | 532 | 236 |
| `EmG` | 4 | 0 |
| `CA7DmG7` | 6 | 1 |
| `GmF` | 7 | 0 |
| `CC7FFm` | 3 | 0 |

Exemplos medidos:

- `Do Or Die` — `D;G;Bm;A;D;G;Bm;A;...` — vocabulário `{D,G,Bm,A}`, sem tag 0;
- `What's Left` — `C;G;C;G;...` — vocabulário `{C,G,Am,F}`, sem tag 1;
- `Samba da Vizinha` — `C;Dm;A7;Dm;G7;...` — vocabulário `{C,Dm,A7,G7}`, sem tag 3.

Nas sequências de 2 acordes (`EmG`, `GmF`) e na `CC7FFm`, todas as músicas com o
vocabulário exato estão na tag; isso não significa que a ordem seja ignorada, e
sim que, nesses casos, existe o bloco contíguo na ordem da sequência.

A interpretação “subsequência ordenada” (ordem sim, contiguidade não) é bem mais
ampla que a tag: 4.763 vs 199 em `BmGDA`, 13.643 vs 4 em `EmG`. Portanto a
contiguidade também é parte do que a tag captura.

### 3.3 Repetição

Repetição não altera a tag:

- a string usada pelo gerador é `acorde1;acorde2;...`; `Gm;F;Gm;F` contém
  `gm;f` na posição 0;
- a condição de vocabulário é sobre conjunto (`set`), então repetir um acorde
  não muda o conjunto.

Exemplo medido: `Marajá` tem `cifra=Gm;F;Gm;F` e `tag=4` (a sequência `GmF`).

A repetição é comum nos dados: 58.904 músicas têm algum token repetido na lista
bruta não vazia (58.906 depois de `limpa_cifra`). `musica.cifra` preserva a
repetição (`main.py:59`, `musica.py:16`); `musica.acordes` a elimina
(`musica.py:17`).

### 3.4 Múltiplas sequências

`get_famosas` devolve um item por sequência que casar; o `''.join` de
`scripts/generate_data_set.py:88` concatenaria os índices. Hoje não há linha com
mais de uma tag (distribuição no apêndice A). Se houvesse, o teste de pertinência
do runtime (`main.py:209`) compararia o índice isolado com uma string concatenada
e a música não apareceria em nenhuma das duas sequências.

## 4. Estruturas disponíveis em tempo de execução

### 4.1 `Musica`

`musica.py:1-25` define os campos:

| Campo | Linha | Conteúdo |
|---|---|---|
| `genero` | `musica.py:13` | gênero |
| `popularidade` | `musica.py:14` | inteiro |
| `tom` | `musica.py:15` | tom |
| `cifra` | `musica.py:16` | lista de acordes na ordem, já passada por `limpa_cifra` |
| `acordes` | `musica.py:17` | `list(set(cifra))` — conjunto, sem ordem nem repetição |
| `seqs_famosas` | `musica.py:18` | lista de tags (ex.: `['0']` ou `['']`) |
| `id_unico_musica` | `musica.py:20` | `id_artista + '_' + id_musica` |
| `url` | `musica.py:22` | `http://www.cifraclub.com.br/<id_artista>/<id_musica>` |

`musica.cifra` é o que preserva ordem e repetição; `musica.acordes` é o que
permite interseção de conjuntos, mas perde as duas coisas.

### 4.2 Índices construídos no carregamento

`main.py:47-98` constrói, uma vez no import:

| Estrutura | Linhas | Uso |
|---|---|---|
| `musicas_dict` | `main.py:47`, `main.py:74` | dicionário por `id_unico_musica` |
| `musicas` | `main.py:88-89` | `OrderedDict` ordenado por popularidade decrescente |
| `genero_musicas` | `main.py:82-85`, `main.py:94-96` | listas por gênero, ordenadas por popularidade |
| `generos` | `main.py:38`, `main.py:66`, `main.py:92` | `set` convertido em lista |
| `acordes` | `main.py:39`, `main.py:77-78` | `set` global de acordes (usado por `/acordes`) |

Não há índice de acorde → músicas. `get_similares` percorre a coleção filtrada e
faz interseção de `set`s por música (`main.py:236-245`); o modo sequência
percorre a mesma coleção e testa a tag (`main.py:208-209`).

### 4.3 O que o CSV carrega

- 67.586 linhas no arquivo; 67.585 carregadas em memória, porque
  `main.py:50` faz `f.readline()` e o arquivo **não tem cabeçalho**. A primeira
  linha descartada é `14-bis_a-qualquer-tempo`.
- 59.444 músicas com cifra não vazia; 8.141 com cifra vazia.
- 6.653 tokens de acorde distintos depois de `limpa_cifra`.
- 52 gêneros distintos; 303 linhas com o gênero literal `R&B;`.

## 5. Normalização: o que existe e o que não existe

### 5.1 Texto

`remover_combinantes` (`main.py:145-147`) faz NFD e remove marcas `Mn`; é usado
apenas em `/search` (`main.py:119` e `main.py:130`). O modo `/similares` não usa
essa função.

### 5.2 Acordes

`limpa_cifra` (`main.py:11-23`) só faz:

- pular tokens vazios (`main.py:14`);
- se o token tem `|`, pegar o primeiro pedaço antes da barra e o primeiro
  token (`main.py:16-18`) — filtro de tablatura;
- caso contrário, dividir por espaços (`main.py:20-22`).

Não há lowercase, remoção de sufixo, unificação de enarmônicos, nem mapeamento de
variações de escrita. `musica.acordes` é `list(set(cifra))` (`musica.py:17`),
portanto também exato e case-sensitive.

O único lowercase do fluxo de sequência está no gerador da tag
(`scripts/generate_data_set.py:12`), que lowercasa a string inteira antes da
substring. Isso torna o **predicado da tag** case-insensitive, mas o valor
armazenado em `musica.cifra`/`musica.acordes` continua com o caso original do
CSV. No runtime, a chave da sequência é case-sensitive (`main.py:194`) e a
interseção do modo `acordes` também (`main.py:240-241`).

### 5.3 Evidência de variações de escrita

Medições no CSV carregado:

| Medida | Valor |
|---|---:|
| tokens limpos distintos | 6.653 |
| grupos de tokens que colidem ao lowercasar | 151 |
| grupos de colisão com `M`/`m` | 96 |
| músicas com algum token de qualquer grupo de colisão | 42.517 |
| músicas com algum token de grupo `M`/`m` | 32.373 |

Exemplos de grupos (formas exatas que convivem no CSV):

- `A#Dim` / `A#dim`
- `A#M` / `A#m`
- `A#M7` / `A#m7`
- `A7(B13)` / `A7(b13)`
- `A7M` / `A7m`
- `A7SUS` / `A7sus`
- `Ab/EB` / `Ab/Eb`

Ou seja: o lowercase do gerador já trata `A#M` e `A#m` como o mesmo token para
fins de tag; o runtime, se comparasse `musica.acordes` diretamente, os trataria
como tokens diferentes.

### 5.4 Efeitos do carregamento

- `replace('"', '').replace('NA', '')` (`main.py:53`) é aplicado à linha inteira,
  não só à cifra. Em 7 títulos o `NA` é removido do meio da palavra:

  | Original | Depois |
  |---|---|
  | `ROTINA DE POBRE` | `ROTI DE POBRE` |
  | `DNA` | `D` |
  | `CABANA` | `CABA` |
  | `She's Got Style (Versão ORIGINAL)` | `She's Got Style (Versão ORIGIL)` |
  | `Surfando Em Karmas e DNA` | `Surfando Em Karmas e D` |
  | `JULIANA` | `JULIA` |
  | `BESTA RUANA` | `BESTA RUA` |

  Na coluna `CIFRA`, `NA` vira `''`, que é o caso pretendido de “sem cifra”; na
  coluna `SEQ_FAMOSA`, `NA` vira `''` e depois `['']` (`main.py:63`).
- `limpa_cifra` altera a lista em 83 músicas quando se compara a lista bruta
  (incluindo entradas vazias) com a lista limpa; 44 quando se comparam apenas os
  tokens não vazios. Desses 44, 6 têm tablatura (`|`) e 38 são acordes separados
  por espaço que viram tokens individuais.
- O CSV tem 52 gêneros; o frontend tem uma constante com 51
  (`static/assets/js/app.js:6-58`). O único gênero do CSV ausente da constante é
  `R&B;` (303 músicas). O endpoint `/generos` devolve os 52.

## 6. Comportamento observado do endpoint

Medições feitas contra o container real (`docker run -p 18080:8080`), com o
mesmo CSV:

| Requisição | Resultado |
|---|---|
| `GET /similares?sequencia=BmGDA` | 100 na página 1; 199 no total (2 páginas) |
| `GET /similares?sequencia=CGAmF` | 100 + 100 + 96; 296 no total (3 páginas) |
| `GET /similares?sequencia=EmG` | 4 (1 página) |
| `GET /similares?sequencia=CA7DmG7` | 5 (1 página) |
| `GET /similares?sequencia=GmF` | 7 (1 página) |
| `GET /similares?sequencia=CC7FFm` | 3 (1 página) |
| `GET /similares?sequencia=bm,g,d,a` | `[]` |
| `GET /similares?sequencia=Bm,G,D,A` | 100 na página 1 (vírgulas removidas) |
| `GET /similares?sequencia=XYZ` | `[]` |
| `GET /similares?sequencia=` | `[]` |
| `GET /generos` | 52 gêneros |
| `Content-Type` de `/similares` | `text/html; charset=utf-8` |

Cada item do modo sequência tem 9 chaves (`main.py:210-220`); o modo `acordes`
tem 12, incluindo `diferenca` e `intersecao` (`main.py:246-258`). O modo
sequência não tem `diferenca`.

### 6.1 Ordem não é determinística entre processos

`generos` é um `set` convertido em lista (`main.py:92`) e `apply_filtro`
concatena os blocos de gênero na ordem dessa lista (`main.py:266-272`). O
`PYTHONHASHSEED` muda a ordem dos blocos e, portanto, o conteúdo da primeira
página. Rodando `research/scripts/ordem_endpoint.py` com seeds diferentes:

| Seed | Primeiros 5 IDs de `BmGDA` (página 1) | Total |
|---|---|---:|
| 0 | `sam-smith_money-on-my-mind`, `laura-pausini_el-no-esta-por-ti`, `laura-pausini_he-creido-en-mi`, `abba_hey-hey-helen`, `hinos-avulsos-ccb_ester` | 199 |
| 1 | `wesley-safadao_sou-ciumento-mesmopart-fernando-e-sorocaba`, `wesley-safadao_segunda-opcao`, `wesley-safadao_lapada-lapada`, `wesley-safadao_vida-de-play-boy`, `wesley-safadao_como-num-filme` | 199 |

O conjunto total é o mesmo; a ordem e o conteúdo de cada página não são. A lista
global de acordes (`main.py:39`, `main.py:77-78`) também muda de ordem entre
processos (`/acordes`).

### 6.2 Ordenação por popularidade

`musicas` é ordenado por popularidade (`main.py:88-89`) e cada
`genero_musicas[genero]` também (`main.py:94-96`), mas `apply_filtro` concatena
blocos de gênero, então a coleção filtrada não é globalmente ordenada por
popularidade. O modo sequência devolve a fatia dessa coleção na ordem dos blocos
(`main.py:196`), sem reordenar. O frontend reordena a página recebida por
`-popularidade` (`static/templates/sequencia.html:42`).

## 7. Fluxo de dados entre componentes

```
[HTML de cifras]
   │  scripts/generate_data_set.py:35-89
   ▼
[data/top/dataset_final.csv]  (9 colunas; coluna 7 = SEQ_FAMOSA)
   │  main.py:49-98 (uma vez, no import)
   ▼
[Musica.cifra]  [Musica.acordes]  [Musica.seqs_famosas]
   │                 │                    │
   │                 │                    └── main.py:208-209 (tag)
   │                 └── main.py:240-245 (modo acordes)
   └── main.py:59 / musica.py:16
   │
   ▼
[/similares]  main.py:170-201
   │  sequencia → main.py:190-197
   ▼
[get_similares_por_sequencia]  main.py:203-223
   │  apply_filtro → main.py:266-272
   ▼
[get_pagina]  main.py:226-228  →  json.dumps  →  AngularJS
   │
   └── static/assets/js/controllers/sequencia.js:63-90
       static/templates/sequencia.html:40-59
```

Pontos de conexão:

- a tag é um artefato **offline**: gerada no build do CSV, não recalculada no
  runtime; por isso uma sequência nova não tem tag e não entra no dicionário
  `sequencias` (`main.py:40-45`);
- `musica.cifra` é a única estrutura que preserva ordem e repetição; `musica.acordes`
  é a única que permite interseção de conjuntos;
- o frontend só conhece 4 das 6 sequências (`static/assets/js/controllers/sequencia.js:2-31`);
- `data/mapeamento_sequencias_famosas.txt` não participa do fluxo.

## 8. Referências de código

| Assunto | Referência |
|---|---|
| Dicionário de sequências | `main.py:40-45` |
| Colunas do CSV | `main.py:25-34` |
| Carregamento do CSV | `main.py:47-98` |
| `limpa_cifra` | `main.py:11-23` |
| `replace('NA','')` | `main.py:53` |
| `seqs_famosas` no carregamento | `main.py:63`, `main.py:69-72` |
| `Musica` | `musica.py:1-25` |
| `musica.cifra` | `musica.py:16` |
| `musica.acordes` | `musica.py:17` |
| `musica.seqs_famosas` | `musica.py:18` |
| `get_famosas` | `scripts/generate_data_set.py:7-24` |
| Atribuição de `famosas` | `scripts/generate_data_set.py:84-89` |
| `/similares` | `main.py:170-201` |
| Modo sequência | `main.py:190-197` |
| `get_similares_por_sequencia` | `main.py:203-223` |
| Teste da tag | `main.py:209` |
| `get_similares` (modo acordes) | `main.py:230-263` |
| `apply_filtro` | `main.py:266-272` |
| `get_pagina` | `main.py:226-228` |
| `TAM_PAGINA` | `main.py:35` |
| `remover_combinantes` | `main.py:145-147` |
| `generos` / `genero_musicas` | `main.py:38`, `main.py:82-85`, `main.py:92-96` |
| `acordes` global | `main.py:39`, `main.py:77-78` |
| Frontend: 4 sequências | `static/assets/js/controllers/sequencia.js:2-31` |
| Frontend: URL | `static/assets/js/controllers/sequencia.js:55-61`, `static/assets/js/controllers/sequencia.js:72-77` |
| Frontend: resultados | `static/templates/sequencia.html:40-59` |
| Rótulos auxiliares | `data/mapeamento_sequencias_famosas.txt:1-6` |

## Apêndice A — medições

Saída de `research/scripts/medicoes_dados.py`:

```
linhas no arquivo: 67586
linhas carregadas (main.py descarta a 1a): 67585
primeira linha (descartada): 14-bis_a-qualquer-tempo
músicas com cifra: 59444
músicas com cifra vazia: 8141
tokens limpos distintos: 6653
grupos de colisão case-insensitive: 151
grupos de colisão com M/m: 96
músicas que contêm algum token em colisão (todos os grupos): 42517
músicas que contêm algum token em colisão M/m: 32373
músicas com token repetido na cifra limpa: 58906
músicas com token repetido na lista bruta não vazia: 58904
músicas em que a lista bruta difere da limpa (incluindo vazios): 83
músicas em que a lista bruta não vazia difere da limpa: 44
músicas com tablatura (|) na cifra: 6
linhas com gênero R&B;: 303
títulos alterados por replace(NA): 7
```

Distribuição de `SEQ_FAMOSA` (saída de `validar_sequencias.py`):

```
[((), 67071), (('1',), 296), (('0',), 199), (('4',), 7), (('3',), 5), (('2',), 4), (('5',), 3)]
```

## Apêndice B — reprodução

```bash
# validação do predicado e da tag (pergunta 2)
PYTHONHASHSEED=0 python3 research/scripts/validar_sequencias.py

# medições do CSV
PYTHONHASHSEED=0 python3 research/scripts/medicoes_dados.py

# ordem dependente do hash seed
PYTHONHASHSEED=0 python3 research/scripts/ordem_endpoint.py
PYTHONHASHSEED=1 python3 research/scripts/ordem_endpoint.py

# API real
docker build -t ciframe .
docker run -p 8080:8080 ciframe
curl 'http://localhost:8080/similares?sequencia=BmGDA'
curl 'http://localhost:8080/similares?sequencia=bm,g,d,a'
curl 'http://localhost:8080/generos'
```
