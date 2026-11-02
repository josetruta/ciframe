# coding: utf-8
import unittest

import matching


class TestMatching(unittest.TestCase):

    def test_sequencia_exata(self):
        self.assertTrue(
            matching.musica_casa_sequencia(
                ["Bm", "G", "D", "A"], ["Bm", "G", "D", "A"]
            )
        )

    def test_ordem_importa(self):
        self.assertFalse(
            matching.musica_casa_sequencia(
                ["A", "D", "G", "Bm"], ["Bm", "G", "D", "A"]
            )
        )

    def test_repeticao_na_musica_nao_invalida(self):
        self.assertTrue(
            matching.musica_casa_sequencia(
                ["Bm", "G", "D", "A", "A"], ["Bm", "G", "D", "A"]
            )
        )

    def test_acorde_extra_na_musica_invalida(self):
        self.assertFalse(
            matching.musica_casa_sequencia(
                ["Bm", "G", "D", "A", "E"], ["Bm", "G", "D", "A"]
            )
        )

    def test_case_insensitive(self):
        self.assertTrue(
            matching.musica_casa_sequencia(
                ["bm", "g", "d", "a"], ["Bm", "G", "D", "A"]
            )
        )

    def test_sequencia_vazia(self):
        self.assertFalse(matching.contigua(["Bm"], []))
        self.assertFalse(matching.musica_casa_sequencia(["Bm"], []))

    def test_sequencia_maior_que_a_musica(self):
        self.assertFalse(
            matching.musica_casa_sequencia(
                ["Bm", "G", "D"], ["Bm", "G", "D", "A"]
            )
        )

    def test_vocabulario_contido(self):
        self.assertTrue(
            matching.vocabulario_contido(
                ["Bm", "G", "D", "A"], ["Bm", "G", "D", "A", "Em"]
            )
        )
        self.assertFalse(
            matching.vocabulario_contido(
                ["Bm", "G", "D", "A"], ["Bm", "G", "D"]
            )
        )

    def test_repeticao_na_sequencia(self):
        self.assertTrue(
            matching.musica_casa_sequencia(
                ["Bm", "G", "D", "A", "A"], ["Bm", "G", "D", "A", "A"]
            )
        )
        self.assertFalse(
            matching.musica_casa_sequencia(
                ["Bm", "G", "D", "A"], ["Bm", "G", "D", "A", "A"]
            )
        )


if __name__ == "__main__":
    unittest.main()
