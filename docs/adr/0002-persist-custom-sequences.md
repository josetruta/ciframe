# Persist the chord-sequence catalog in SQLite inside the single local container

The sequence catalog lived in code: six keys hardcoded in `main.py` and four cards
hardcoded in the `#/porsequencia` controller, with matches coming from a
precomputed `SEQ_FAMOSA` column in the CSV. There is no database. The CSV is read
once at import into memory, the `Dockerfile` declares no `VOLUME`, and the
documented `docker run` mounts nothing. A file written in the container survives
`docker stop`/`docker start` of that same container and is gone after `docker rm`
plus a new `docker run`. A catalog that visitors can grow has to outlive that,
without a new deploy and without a second service.

We will persist only the sequence catalog in SQLite, through the `sqlite3` module
already in the `python:3.9-slim` image (SQLite 3.46.1; the `sqlite3` CLI is not
present and is not required). The file lives on a dedicated path such as
`/app/db/sequences.db`, with a named volume mounted at `/app/db`. Startup creates
the schema if needed and seeds the six original sequences. Songs and genres stay
in the in-memory CSV. The app remains the single local container from
`docs/adr/0001-local-only-docker-deploy.md`: no new Python dependency, no
Postgres/MySQL/Redis/Mongo, and responses stay `json.dumps(...)`.

SQLite was chosen over a JSON file because the catalog needs a unique key,
transactions, and queries, which a hand-rolled atomic write does not give.
External databases were rejected because they need another container, a driver,
and their own volume, which breaks the single-container deploy. The writable
layer alone was rejected because removing the container drops it. Mounting the
volume on `/app` itself would hide the image contents, including the CSV, so the
database directory stays separate from `/app/data`.

The cost is a documented change to `docker run` (`-v ciframe-db:/app/db`, or an
equivalent `VOLUME`): without that mount, `docker rm` still loses the catalog.

The implementation keeps one `sequences` table: `chords_json` holds the ordered
chord array, `normalized_key` (lowercase chords joined by commas) is unique and
backs duplicate detection (`409` with the existing id), and `created_at` records
creation time. Startup uses `CREATE TABLE IF NOT EXISTS` and seeds the six
original sequences idempotently. Schema versioning/migrations are still future
work; gunicorn currently runs one worker, which keeps SQLite write pressure low
until the worker count changes.
