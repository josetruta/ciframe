# coding: utf-8
import json
import os
import tempfile
import unittest

import db
import matching

# main.py inicializa o banco no import; usa um caminho temporário para não
# sujar o banco de desenvolvimento.
_BOOTSTRAP = tempfile.TemporaryDirectory()
db.DB_PATH = os.path.join(_BOOTSTRAP.name, "bootstrap.db")

import main  # noqa: E402  (precisa vir depois de configurar db.DB_PATH)


def tearDownModule():
    _BOOTSTRAP.cleanup()


class TestAPI(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self._old_db_path = db.DB_PATH
        db.DB_PATH = os.path.join(self.tmp.name, "test.db")
        db.init_db()
        self.client = main.app.test_client()

    def tearDown(self):
        db.DB_PATH = self._old_db_path
        self.tmp.cleanup()

    def _get_json(self, path):
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200)
        return json.loads(response.get_data(as_text=True))

    def _todas_paginas(self, sequencia):
        resultados = []
        pagina = 1
        while True:
            data = self._get_json(
                "/similares?sequencia=%s&pagina=%s" % (sequencia, pagina)
            )
            if not data:
                break
            resultados.extend(data)
            pagina += 1
        return resultados

    def _golden_sets(self):
        return [
            {
                musica.id_unico_musica
                for musica in main.musicas.values()
                if str(indice) in musica.seqs_famosas
            }
            for indice in range(6)
        ]

    def test_catalogo_inicial(self):
        response = self.client.get("/sequencias")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.content_type.startswith("text/html"))
        catalogo = json.loads(response.get_data(as_text=True))
        self.assertEqual(len(catalogo), 6)
        self.assertEqual(catalogo[0]["acordes"], ["Bm", "G", "D", "A"])
        self.assertIn("id", catalogo[0])

    def test_golden_sets(self):
        catalogo = self._get_json("/sequencias")
        esperados = self._golden_sets()
        self.assertEqual([len(conjunto) for conjunto in esperados],
                         [199, 296, 4, 5, 7, 3])
        self.assertEqual(sum(len(conjunto) for conjunto in esperados), 514)

        for indice, sequencia in enumerate(catalogo):
            resultados = self._todas_paginas(sequencia["id"])
            ids = [resultado["id_unico_musica"] for resultado in resultados]
            self.assertEqual(
                len(ids),
                len(set(ids)),
                "duplicatas em %s" % sequencia["acordes"],
            )
            self.assertEqual(
                set(ids),
                esperados[indice],
                "sequencia %s" % sequencia["acordes"],
            )

    def test_paginacao(self):
        catalogo = self._get_json("/sequencias")
        seq0 = catalogo[0]["id"]
        seq1 = catalogo[1]["id"]

        self.assertEqual(
            [
                len(self._get_json(
                    "/similares?sequencia=%s&pagina=%s" % (seq0, pagina)
                ))
                for pagina in (1, 2, 3)
            ],
            [100, 99, 0],
        )
        self.assertEqual(
            [
                len(self._get_json(
                    "/similares?sequencia=%s&pagina=%s" % (seq1, pagina)
                ))
                for pagina in (1, 2, 3, 4)
            ],
            [100, 100, 96, 0],
        )

    def test_formato(self):
        seq0 = self._get_json("/sequencias")[0]["id"]
        response = self.client.get("/similares?sequencia=%s" % seq0)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.content_type.startswith("text/html"))
        data = json.loads(response.get_data(as_text=True))
        self.assertTrue(data)
        self.assertEqual(
            set(data[0].keys()),
            {
                "id_unico_musica",
                "id_artista",
                "id_musica",
                "nome_artista",
                "nome_musica",
                "popularidade",
                "acordes",
                "genero",
                "url",
            },
        )
        self.assertNotIn("diferenca", data[0])

    def test_criar_sequencia(self):
        response = self.client.post(
            "/sequencias", json={"acordes": ["D", "A", "Bm", "G"]}
        )
        self.assertEqual(response.status_code, 201)
        criada = json.loads(response.get_data(as_text=True))
        self.assertEqual(criada["acordes"], ["D", "A", "Bm", "G"])

        catalogo = self._get_json("/sequencias")
        self.assertEqual(len(catalogo), 7)
        self.assertEqual(catalogo[-1]["id"], criada["id"])

    def test_duplicata(self):
        response = self.client.post(
            "/sequencias", json={"acordes": ["Bm", "G", "D", "A"]}
        )
        self.assertEqual(response.status_code, 409)
        erro = json.loads(response.get_data(as_text=True))
        self.assertEqual(erro["id"], 1)

    def test_payload_invalido(self):
        payloads = [
            {},
            {"acordes": []},
            {"acordes": "Bm"},
            {"acordes": ["Bm", 1]},
            {"acordes": ["Bm"] * 21},
            {"acordes": [""]},
            {"acordes": ["B" * 21]},
        ]
        for payload in payloads:
            response = self.client.post("/sequencias", json=payload)
            self.assertEqual(response.status_code, 400, payload)

    def test_alias_legado(self):
        catalogo = self._get_json("/sequencias")
        seq0 = catalogo[0]
        por_id = {
            resultado["id_unico_musica"]
            for resultado in self._todas_paginas(seq0["id"])
        }
        por_chave = {
            resultado["id_unico_musica"]
            for resultado in self._todas_paginas("BmGDA")
        }
        por_virgulas = {
            resultado["id_unico_musica"]
            for resultado in self._todas_paginas("Bm,G,D,A")
        }

        self.assertEqual(por_id, por_chave)
        self.assertEqual(por_id, por_virgulas)
        self.assertEqual(self._get_json("/similares?sequencia=bm,g,d,a"), [])

    def test_sequencia_customizada(self):
        acordes = ["Bm", "G", "D", "A", "Em"]
        response = self.client.post("/sequencias", json={"acordes": acordes})
        self.assertEqual(response.status_code, 201)
        criada = json.loads(response.get_data(as_text=True))

        esperado = {
            musica.id_unico_musica
            for musica in main.musicas.values()
            if matching.musica_casa_sequencia(musica.cifra, acordes)
        }
        self.assertTrue(esperado)

        resultados = self._todas_paginas(criada["id"])
        self.assertEqual(
            {resultado["id_unico_musica"] for resultado in resultados},
            esperado,
        )

    def test_filtro_genero(self):
        seq0 = self._get_json("/sequencias")[0]["id"]
        data = self._get_json(
            "/similares?sequencia=%s&generos=Rock" % seq0
        )
        self.assertTrue(all(item["genero"] == "Rock" for item in data))

    def test_sequencia_inexistente(self):
        self.assertEqual(self._get_json("/similares?sequencia=9999"), [])
        self.assertEqual(self._get_json("/similares?sequencia=NaoExiste"), [])


if __name__ == "__main__":
    unittest.main()
