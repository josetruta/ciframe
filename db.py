# coding: utf-8
"""Catálogo de sequências de acordes em SQLite.

O banco guarda apenas as sequências. Músicas e gêneros continuam no CSV em
memória (`main.py`). O caminho pode ser sobrescrito por `DECIFRAME_DB` ou, em
testes, pela atribuição direta de `db.DB_PATH`.
"""
import json
import os
import sqlite3


_DB_PATH_PADRAO = os.path.join("db", "sequences.db")
DB_PATH = None

SEQUENCIAS_ORIGINAIS = [
    ["Bm", "G", "D", "A"],
    ["C", "G", "Am", "F"],
    ["Em", "G"],
    ["C", "A7", "Dm", "G7"],
    ["Gm", "F"],
    ["C", "C7", "F", "Fm"],
]

# As chaves que o endpoint aceitava antes do catálogo, na mesma ordem da tag
# `seqs_famosas` (0..5).
ALIASES_LEGADOS = {
    "BmGDA": "bm,g,d,a",
    "CGAmF": "c,g,am,f",
    "EmG": "em,g",
    "CA7DmG7": "c,a7,dm,g7",
    "GmF": "gm,f",
    "CC7FFm": "c,c7,f,fm",
}


class SequenciaDuplicada(Exception):
    """A sequência já existe; `id_existente` aponta para a linha existente."""

    def __init__(self, id_existente=None):
        self.id_existente = id_existente
        super().__init__("sequencia ja existe")


def _caminho():
    if DB_PATH is not None:
        return DB_PATH
    return os.environ.get("DECIFRAME_DB", _DB_PATH_PADRAO)


def _conecta():
    caminho = _caminho()
    diretorio = os.path.dirname(caminho)
    if diretorio:
        os.makedirs(diretorio, exist_ok=True)
    conexao = sqlite3.connect(caminho, timeout=10)
    conexao.row_factory = sqlite3.Row
    return conexao


def _chave_normalizada(acordes):
    return ",".join(acorde.strip().lower() for acorde in acordes)


def _linha_para_sequencia(linha):
    return {"id": linha["id"], "acordes": json.loads(linha["chords_json"])}


def _inserir(conexao, acordes):
    conexao.execute(
        "INSERT OR IGNORE INTO sequences (chords_json, normalized_key) "
        "VALUES (?, ?)",
        (
            json.dumps(list(acordes), ensure_ascii=False),
            _chave_normalizada(acordes),
        ),
    )


def init_db():
    """Cria o schema, se necessário, e semeia as 6 sequências originais."""
    conexao = _conecta()
    try:
        conexao.execute(
            """
            CREATE TABLE IF NOT EXISTS sequences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chords_json TEXT NOT NULL,
                normalized_key TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )
        for acordes in SEQUENCIAS_ORIGINAIS:
            _inserir(conexao, acordes)
        conexao.commit()
    finally:
        conexao.close()


def listar_sequencias():
    conexao = _conecta()
    try:
        linhas = conexao.execute(
            "SELECT id, chords_json FROM sequences ORDER BY id"
        ).fetchall()
        return [_linha_para_sequencia(linha) for linha in linhas]
    finally:
        conexao.close()


def criar_sequencia(acordes):
    chave = _chave_normalizada(acordes)
    conexao = _conecta()
    try:
        try:
            cursor = conexao.execute(
                "INSERT INTO sequences (chords_json, normalized_key) "
                "VALUES (?, ?)",
                (
                    json.dumps(list(acordes), ensure_ascii=False),
                    chave,
                ),
            )
            conexao.commit()
            return {"id": cursor.lastrowid, "acordes": list(acordes)}
        except sqlite3.IntegrityError:
            conexao.rollback()
            linha = conexao.execute(
                "SELECT id FROM sequences WHERE normalized_key = ?", (chave,)
            ).fetchone()
            raise SequenciaDuplicada(linha["id"] if linha else None)
    finally:
        conexao.close()


def buscar_sequencia(id_seq):
    conexao = _conecta()
    try:
        linha = conexao.execute(
            "SELECT id, chords_json FROM sequences WHERE id = ?", (id_seq,)
        ).fetchone()
        return _linha_para_sequencia(linha) if linha else None
    finally:
        conexao.close()


def _buscar_por_chave(chave):
    conexao = _conecta()
    try:
        linha = conexao.execute(
            "SELECT id, chords_json FROM sequences WHERE normalized_key = ?",
            (chave,),
        ).fetchone()
        return _linha_para_sequencia(linha) if linha else None
    finally:
        conexao.close()


def buscar_por_alias_legado(chave):
    """Resolve `BmGDA` ou `Bm,G,D,A` para a sequência semeada correspondente."""
    if not chave:
        return None
    normalizada = chave.replace(",", "").replace(" ", "")
    chave_normalizada = ALIASES_LEGADOS.get(normalizada)
    if chave_normalizada is None:
        return None
    return _buscar_por_chave(chave_normalizada)
