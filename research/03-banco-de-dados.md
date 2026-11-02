# Pesquisa 3 — Bancos embarcados no container único e persistência

> Documento descritivo do código em `fb97001` (2026-10-17). Não contém proposta,
> avaliação ou trabalho futuro. As referências usam `caminho/arquivo.ext:linha`.

## Escopo e método

Pergunta respondida: a pergunta 3 de
`docs/features/sequencias-customizadas/01-research.md:21-25` — quais bancos
embarcados (sem serviço externo adicional) existem/operam dentro do container
Docker único e local-only documentado em
`docs/adr/0001-local-only-docker-deploy.md`, e o que cada opção implica para o
`Dockerfile` atual e para a persistência entre reinícios do container.

Método:

- leitura integral de `Dockerfile`, `requirements.txt`, `README.md`, `AGENTS.md`,
  `docs/adr/0001-local-only-docker-deploy.md`,
  `docs/adr/0002-persist-custom-sequences.md` e `main.py`;
- busca por arquivos de banco, migrations, compose e drivers;
- build real da imagem (`docker build -t ciframe-research .`) e execução do
  container;
- inspeção do ambiente dentro da imagem `python:3.9-slim` (módulos e binários);
- experimento de persistência com `docker stop`/`docker start` e com
  `docker rm` + novo `docker run`;
- verificação do default de workers do gunicorn 23.0.0.

## Sumário

Hoje **não existe banco de dados**: o `README.md:8-9` descreve “uma base de dados
carregada de um CSV em memória (sem banco)” e o `AGENTS.md:9-11` repete “there is
no database”; o `main.py:49-98` abre `data/top/dataset_final.csv` em modo leitura,
carrega tudo em estruturas Python no import e fecha o arquivo. O `Dockerfile` não
tem `VOLUME`, não declara `USER` e o `README.md:15-18` executa
`docker run -p 8080:8080 ciframe` sem `-v`; a imagem resultante tem
`Volumes=null` e o container em execução tem `Mounts=[]`. Dentro do ambiente
atual, sem serviço externo, já estão disponíveis o módulo `sqlite3` da stdlib
(biblioteca SQLite 3.46.1 na imagem `python:3.9-slim`, mas **sem** o binário
`sqlite3` de linha de comando), `dbm`/`shelve` e arquivos JSON/CSV/pickle; nenhum
deles é usado hoje. A persistência depende de onde o arquivo é gravado: a camada
gravável do container sobrevive a `docker stop` + `docker start` do mesmo
container, mas é destruída por `docker rm`; um novo `docker run` parte da imagem e
não vê arquivos criados em execuções anteriores. O `AGENTS.md:45` registra que
editar `data/top/*.csv` exige restart porque o CSV é lido uma vez no import.

## 1. Estado atual: nenhum banco

### 1.1 O que o código carrega

`main.py:47-98` constrói tudo no import do módulo:

| Estrutura | Linhas | Conteúdo |
|---|---|---|
| `musicas_dict` | `main.py:47`, `main.py:74` | dicionário por `id_unico_musica` |
| `musicas` | `main.py:88-89` | `OrderedDict` ordenado por popularidade |
| `genero_musicas` | `main.py:82-85`, `main.py:94-96` | listas por gênero |
| `generos` | `main.py:38`, `main.py:66`, `main.py:92` | `set` convertido em lista |
| `acordes` | `main.py:39`, `main.py:77-78` | `set` global de acordes |

O arquivo é aberto em `main.py:49` com `open('data/top/dataset_final.csv')`
(sem modo de escrita), lido no laço `main.py:52-98` e fechado em `main.py:98`.
Não há `INSERT`, `UPDATE`, `CREATE TABLE`, migrations, ORM ou conexão de banco em
nenhum ponto do backend.

### 1.2 O que existe no repositório

Buscas no repositório (excluindo `.git`) não encontram:

- arquivos `*.db`, `*.sqlite*` ou `*.sql`;
- `docker-compose*`;
- `alembic*` ou diretório `migrations`;
- driver de banco em `requirements.txt` (só `Flask==3.1.3` e
  `gunicorn==23.0.0`, `requirements.txt:4-5`).

O `README.md:8-9` e o `AGENTS.md:9-11` descrevem explicitamente a ausência de
banco. O `AGENTS.md:45` registra que o CSV é lido uma vez no import, então
alterações no CSV exigem restart (e, no Docker, rebuild da imagem, porque o CSV é
copiado no build — `Dockerfile:8`).

## 2. Ambiente real do container

### 2.1 Dockerfile

`Dockerfile:1-12`:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

CMD ["gunicorn", "--bind", "0.0.0.0:8080", "main:app"]
```

Fatos relevantes:

- não há `VOLUME`, `USER`, `RUN mkdir` de dados, inicialização de banco ou
  migrations;
- não há `--workers` no `CMD`; o default do gunicorn 23.0.0 é **1 worker**
  (verificado com `gunicorn.config.Config().workers`);
- `WORKDIR /app` (`Dockerfile:3`) faz o caminho relativo
  `data/top/dataset_final.csv` (`main.py:49`) resolver para
  `/app/data/top/dataset_final.csv`;
- `COPY . .` (`Dockerfile:8`) copia o contexto do build para `/app`; o
  `.dockerignore` tem apenas `.git`, `.venv`, `__pycache__` e `*.pyc`
  (`.dockerignore:1-4`), então um arquivo de banco presente no contexto seria
  copiado para a imagem;
- `pip install` (`Dockerfile:6`) acontece antes do `COPY . .`
  (`Dockerfile:8`): mudanças em `requirements.txt` invalidam a camada de
  dependências; mudanças de código invalidam a partir do `COPY`.

### 2.2 O que a imagem contém

Inspeção da imagem `python:3.9-slim` usada pelo `FROM`:

| Item | Resultado |
|---|---|
| Python | 3.9.25 |
| módulo `sqlite3` | disponível; biblioteca SQLite 3.46.1 |
| binário `sqlite3` (CLI) | **ausente** (`command -v sqlite3` não encontra) |
| `dbm` | disponível |
| `shelve` | disponível |
| usuário | `root` (`Config.User` vazio) |
| `WorkingDir` | `/app` |
| `Volumes` da imagem | `null` |
| tamanho da imagem construída | 240 MB |
| CSV dentro da imagem | 15.866.887 bytes em `/app/data/top/dataset_final.csv` |

O container em execução:

- `Mounts=[]` (nenhum volume ou bind mount);
- `/app` é gravável: `touch /app/.write-test` funcionou;
- `docker diff` após o startup mostrou apenas `__pycache__` (bytecode de
  `main.py`/`musica.py` e da stdlib), nenhum arquivo de dados da aplicação.

### 2.3 Gunicorn

O `CMD` (`Dockerfile:12`) não passa `--workers`; o default do gunicorn 23.0.0 é
1 worker. Hoje há um único processo de aplicação servindo as requisições, e o CSV
é lido uma vez por processo. O `docker run` do `README.md:17` publica apenas a
porta 8080 (`-p 8080:8080`), sem `-v`.

## 3. Opções embarcadas presentes no ambiente atual

A classificação abaixo é factual: “sem serviço externo” significa que o recurso
já está disponível na imagem e não exige um segundo container/serviço.

### 3.1 `sqlite3` (módulo da stdlib)

- **O que é**: módulo `sqlite3` do CPython, que fala com uma biblioteca SQLite
  embutida; o banco é um arquivo local.
- **Serviço externo**: não.
- **Dependência nova**: não (stdlib do Python 3.9; já presente na imagem).
- **CLI**: o binário `sqlite3` não está na imagem; a operação teria que ser via
  Python ou seria necessário instalar o pacote do sistema.
- **Onde o dado vive**: um arquivo, por exemplo em `/app/...` (gravável) ou em
  um caminho montado.
- **Dockerfile**: nenhuma mudança obrigatória para usar o módulo; uma mudança
  seria necessária apenas para declarar `VOLUME`, criar diretório ou instalar o
  CLI.
- **Persistência**: com o arquivo na camada gravável, sobrevive a
  `docker stop`/`docker start` do mesmo container e é perdido em `docker rm` +
  novo `docker run`; com um volume nomeado ou bind mount, sobrevive à remoção do
  container (enquanto o volume/host path existir).

### 3.2 `dbm` / `shelve` (stdlib)

- **O que é**: `dbm` é uma interface chave-valor sobre implementações de banco
  embutido; `shelve` usa `dbm` + `pickle` para persistir objetos Python.
- **Serviço externo**: não.
- **Dependência nova**: não (stdlib; `import dbm` funciona na imagem).
- **Onde o dado vive**: um ou mais arquivos locais.
- **Dockerfile**: nenhuma mudança obrigatória; mesmas considerações de caminho
  e volume do `sqlite3`.
- **Persistência**: a mesma mecânica de arquivo da §3.1 (camada gravável vs
  volume/bind mount).

### 3.3 Arquivos JSON / CSV / pickle

- **O que é**: serialização em arquivo texto/binário com módulos da stdlib
  (`json`, `csv`, `pickle`).
- **Serviço externo**: não.
- **Dependência nova**: não.
- **Onde o dado vive**: um arquivo local.
- **Dockerfile**: nenhuma mudança obrigatória; mesmas considerações de caminho
  e volume.
- **Persistência**: a mesma mecânica de arquivo da §3.1.

### 3.4 Estruturas em memória (estado atual)

- **O que é**: os dicionários/listas/sets construídos em `main.py:47-98`
  (`musicas_dict`, `musicas`, `genero_musicas`, `generos`, `acordes`).
- **Serviço externo**: não.
- **Dependência nova**: não.
- **Onde o dado vive**: RAM do processo.
- **Dockerfile**: nenhuma mudança.
- **Persistência**: nenhuma entre reinícios do processo ou do container; o CSV
  é relido no próximo import (`main.py:49-98`). É o que existe hoje.

### 3.5 Opções que exigem serviço externo

PostgreSQL, MySQL, Redis e MongoDB **não** são embarcados no sentido da pergunta:
exigem um serviço/container adicional, driver no `requirements.txt` e configuração
de rede/credenciais. Hoje:

- não há driver para nenhum deles em `requirements.txt:4-5`;
- não há `docker-compose` nem segundo serviço no repositório;
- o `Dockerfile` descreve um único processo gunicorn (`Dockerfile:12`) e o
  `README.md:15-18` um único `docker run`;
- o `docs/adr/0001-local-only-docker-deploy.md:9-12` descreve “a single
  `Dockerfile` that runs the app locally via gunicorn” e a arquitetura existente
  (“single `main.py`, in-memory CSV-backed search, Python 3.9”).

## 4. Implicações para o `Dockerfile` atual

### 4.1 Opções da stdlib (sqlite3, dbm/shelve, JSON/CSV/pickle)

- **`requirements.txt`**: nenhuma linha nova.
- **`Dockerfile`**: nenhuma linha obrigatória para o módulo; o arquivo pode ser
  criado em `/app` (gravável) ou em um caminho montado. Se o caminho for um
  diretório novo, seria necessário `RUN mkdir`/`chown`; se o dado precisar
  sobreviver a `docker rm`, seria necessário `VOLUME` e/ou `-v` no `docker run`.
- **Build**: `COPY . .` (`Dockerfile:8`) copiaria um arquivo de banco que
  estivesse no contexto; o `.dockerignore` não exclui `*.db`/`*.sqlite*`
  (`.dockerignore:1-4`).
- **Runtime**: o processo roda como `root` e `/app` é gravável, então a criação
  do arquivo funciona sem ajuste de permissão.
- **Camadas**: uma dependência nova invalidaria a camada de `pip install`
  (`Dockerfile:6`); um arquivo de dados novo não afeta essa camada, só o
  `COPY . .`.

### 4.2 Opções com serviço externo

- **`requirements.txt`**: exigiria o driver correspondente.
- **`Dockerfile`**: exigiria uma imagem/serviço adicional (ou um `docker run`
  separado), porta, rede, variáveis de ambiente e um volume para o serviço.
- **Persistência**: ficaria no volume do serviço, não na camada gravável do
  container da aplicação.
- **Estado atual**: nada disso existe no repositório; o `Dockerfile` e o
  `README.md` descrevem um único container local.

## 5. Persistência entre reinícios do container

### 5.1 Mecânica do Docker

- A camada gravável do container é preservada por `docker stop` + `docker start`
  do **mesmo** container e por `docker restart`.
- A camada gravável é destruída por `docker rm`; um novo `docker run` cria um
  container novo a partir da imagem.
- Volumes nomeados e bind mounts ficam fora da camada gravável e sobrevivem à
  remoção do container, enquanto o volume/host path existir.
- A documentação do Docker descreve volumes como “persistent data stores for
  containers” e a camada gravável como destruída junto com o container
  (https://docs.docker.com/engine/storage/volumes/).

### 5.2 Experimento realizado

Com o container `ciframe-research` em execução:

```bash
docker exec ciframe-research sh -c 'echo hello > /app/persist-test'
docker stop ciframe-research && docker start ciframe-research
docker exec ciframe-research sh -c 'cat /app/persist-test'
# hello

docker rm -f ciframe-research
docker run -d --name ciframe-research-2 -p 18080:8080 ciframe-research
docker exec ciframe-research-2 sh -c 'cat /app/persist-test'
# MISSING
```

Resultados:

| Operação | `/app/persist-test` |
|---|---|
| `docker stop` + `docker start` (mesmo container) | presente (`hello`) |
| `docker rm` + novo `docker run` | ausente (`MISSING`) |
| `docker inspect` do container | `Mounts=[]` |
| `docker inspect` da imagem | `Volumes=null` |
| `README.md:17` | `docker run -p 8080:8080 ciframe` (sem `-v`) |

### 5.3 O que o app grava hoje

`docker diff` após o startup mostrou apenas `__pycache__`:

```
A /app/__pycache__
A /app/__pycache__/main.cpython-39.pyc
A /app/__pycache__/musica.cpython-39.pyc
A /usr/local/lib/python3.9/.../__pycache__/...
```

Não há arquivo de dados, banco, cache de aplicação ou log sendo gravado pelo
código. O CSV é aberto em modo leitura (`main.py:49`) e o `f.close()` está em
`main.py:98`. Portanto, hoje não existe dado de aplicação a persistir; as únicas
escritas são bytecode descartável.

### 5.4 Observação sobre montar um volume em `/app`

O CSV está em `/app/data/top/dataset_final.csv` (por causa de
`Dockerfile:3` + `main.py:49`). Montar um volume/bind mount diretamente em
`/app` sobrepõe o conteúdo da imagem nesse diretório; um volume nomeado novo é
populado com o conteúdo da imagem no primeiro uso, enquanto um bind mount não
copia nada e simplesmente mostra o conteúdo do host. Isso é relevante para
qualquer arquivo de banco colocado em `/app`: o caminho do CSV e o caminho do
banco precisam coexistir com o que for montado.

## 6. Matriz de implicações

| Opção | Serviço externo | Dependência nova | Onde o dado vive | Mudança no `Dockerfile` | `stop`/`start` | `rm` + novo `run` |
|---|---|---|---|---|---|---|
| `sqlite3` (stdlib) | não | não | arquivo | nenhuma obrigatória; `VOLUME`/`-v` para persistir | sobrevive (camada gravável) | perde, salvo volume/bind |
| `dbm`/`shelve` (stdlib) | não | não | arquivo | idem | sobrevive | perde, salvo volume/bind |
| JSON/CSV/pickle | não | não | arquivo | idem | sobrevive | perde, salvo volume/bind |
| em memória (atual) | não | não | RAM | nenhuma | perde no restart do processo | perde |
| PostgreSQL/MySQL/Redis/MongoDB | sim | sim (driver) | serviço | nova imagem/serviço/rede/volume | depende do serviço | depende do volume do serviço |

“Sobrevive (camada gravável)” significa que o arquivo está no filesystem do
container e o mesmo container foi apenas parado e iniciado; “perde, salvo
volume/bind” significa que `docker rm` destrói a camada gravável.

## 7. O que os documentos existentes registram

- `README.md:8-9`: “backend Flask (Python) servindo uma API JSON + um frontend
  AngularJS estático, numa base de dados carregada de um CSV em memória (sem
  banco)”.
- `AGENTS.md:9-11`: “Single file (`main.py`) that loads
  `data/top/dataset_final.csv` into memory once at startup — there is no
  database.”
- `AGENTS.md:16`: “Deploy: local-only via Docker for now. No cloud target has
  been chosen.”
- `AGENTS.md:45`: “Editing `data/top/*.csv` requires a restart: it's read once at
  import time, not per-request.”
- `docs/adr/0001-local-only-docker-deploy.md:9-12`: substituição das configs
  mortas de App Engine/Heroku por “a single `Dockerfile` that runs the app
  locally via gunicorn”; o backend mantém “single `main.py`, in-memory
  CSV-backed search, Python 3.9”; o alvo de nuvem ficou “intentionally left
  undecided” (`docs/adr/0001-local-only-docker-deploy.md:14-16`).
- `docs/adr/0002-persist-custom-sequences.md:1-8`: é um **template não
  preenchido** (“[Título: decisão de introduzir persistência para sequências de
  acordes customizadas]” e “[seu texto aqui]”); não há decisão registrada sobre
  persistência.

## 8. Comandos de verificação

```bash
# build e execução
docker build -t ciframe-research .
docker run -d --name ciframe-research -p 18080:8080 ciframe-research

# ambiente
docker inspect ciframe-research:latest \
  --format 'Volumes={{json .Config.Volumes}} User={{json .Config.User}} WorkingDir={{json .Config.WorkingDir}} Cmd={{json .Config.Cmd}}'
docker exec ciframe-research sh -c \
  'python -c "import sqlite3,sys; print(sys.version.split()[0], sqlite3.sqlite_version)"; command -v sqlite3 || echo absent; python -c "import dbm; print(\"dbm ok\")"'

# escritas em runtime
docker diff ciframe-research

# persistência
docker exec ciframe-research sh -c 'echo hello > /app/persist-test'
docker stop ciframe-research && docker start ciframe-research
docker exec ciframe-research sh -c 'cat /app/persist-test'
docker rm -f ciframe-research
docker run -d --name ciframe-research-2 -p 18080:8080 ciframe-research
docker exec ciframe-research-2 sh -c 'cat /app/persist-test || echo MISSING'

# default de workers do gunicorn 23.0.0
python3 -m venv /tmp/gvenv && /tmp/gvenv/bin/pip install -q gunicorn==23.0.0
/tmp/gvenv/bin/python -c "from gunicorn.config import Config; print(Config().workers)"
```

## 9. Referências de código

| Assunto | Referência |
|---|---|
| `FROM` / `WORKDIR` | `Dockerfile:1-3` |
| `COPY requirements.txt` / `pip install` | `Dockerfile:5-6` |
| `COPY . .` | `Dockerfile:8` |
| `EXPOSE` / `CMD` | `Dockerfile:10-12` |
| Dependências | `requirements.txt:4-5` |
| `.dockerignore` | `.dockerignore:1-4` |
| Leitura do CSV | `main.py:49-98` |
| Estruturas em memória | `main.py:47-98` |
| `README` (sem banco) | `README.md:8-9` |
| `README` (run) | `README.md:15-18` |
| `AGENTS.md` (sem banco) | `AGENTS.md:9-11` |
| `AGENTS.md` (restart do CSV) | `AGENTS.md:45` |
| ADR 0001 | `docs/adr/0001-local-only-docker-deploy.md:9-16` |
| ADR 0002 (template) | `docs/adr/0002-persist-custom-sequences.md:1-8` |
| Docker volumes | https://docs.docker.com/engine/storage/volumes/ |
