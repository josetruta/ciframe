# coding: utf-8
import os
import tempfile
import unittest

import db


class TestDB(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self._old_db_path = db.DB_PATH
        db.DB_PATH = os.path.join(self.tmp.name, "sequences.db")
        db.init_db()

    def tearDown(self):
        db.DB_PATH = self._old_db_path
        self.tmp.cleanup()

    def test_seed(self):
        sequencias = db.listar_sequencias()
        self.assertEqual(
            [sequencia["acordes"] for sequencia in sequencias],
            db.SEQUENCIAS_ORIGINAIS,
        )
        self.assertEqual(len(sequencias), 6)

    def test_init_idempotente(self):
        db.init_db()
        self.assertEqual(len(db.listar_sequencias()), 6)

    def test_criar_e_buscar(self):
        criada = db.criar_sequencia(["D", "A", "Bm", "G"])
        self.assertEqual(criada["acordes"], ["D", "A", "Bm", "G"])
        encontrada = db.buscar_sequencia(criada["id"])
        self.assertEqual(encontrada["acordes"], ["D", "A", "Bm", "G"])

    def test_duplicata(self):
        with self.assertRaises(db.SequenciaDuplicada) as contexto:
            db.criar_sequencia(["Bm", "G", "D", "A"])
        self.assertEqual(contexto.exception.id_existente, 1)

    def test_duplicata_normalizada(self):
        with self.assertRaises(db.SequenciaDuplicada):
            db.criar_sequencia(["bm", "g", "d", "a"])

    def test_alias_legado(self):
        self.assertEqual(
            db.buscar_por_alias_legado("BmGDA")["acordes"],
            ["Bm", "G", "D", "A"],
        )
        self.assertEqual(
            db.buscar_por_alias_legado("Bm,G,D,A")["acordes"],
            ["Bm", "G", "D", "A"],
        )
        self.assertIsNone(db.buscar_por_alias_legado("bm,g,d,a"))

    def test_alias_legado_todas(self):
        chaves = ["BmGDA", "CGAmF", "EmG", "CA7DmG7", "GmF", "CC7FFm"]
        for chave, acordes in zip(chaves, db.SEQUENCIAS_ORIGINAIS):
            self.assertEqual(db.buscar_por_alias_legado(chave)["acordes"], acordes)

    def test_busca_inexistente(self):
        self.assertIsNone(db.buscar_sequencia(9999))
        self.assertIsNone(db.buscar_por_alias_legado("NaoExiste"))


if __name__ == "__main__":
    unittest.main()
