# coding: utf-8
"""Matching de sequências de acordes.

O predicado reproduz o que `get_famosas` fazia na geração do CSV
(`scripts/generate_data_set.py:7-24`): a sequência precisa aparecer como um
bloco contíguo de acordes e todos os acordes da música precisam pertencer ao
vocabulário da sequência. A comparação é case-insensitive; não há normalização
de sufixos/enarmônicos.
"""


def _minusculo(acordes):
    return [acorde.lower() for acorde in acordes]


def contigua(cifra, sequencia):
    """True se `sequencia` aparece como bloco contíguo em `cifra`."""
    musica = _minusculo(cifra)
    alvo = _minusculo(sequencia)
    tamanho = len(alvo)
    if tamanho == 0 or tamanho > len(musica):
        return False
    return any(
        musica[i:i + tamanho] == alvo
        for i in range(len(musica) - tamanho + 1)
    )


def vocabulario_contido(cifra, sequencia):
    """True se todo acorde da música também está na sequência."""
    return {acorde.lower() for acorde in cifra} <= {
        acorde.lower() for acorde in sequencia
    }


def musica_casa_sequencia(cifra, sequencia):
    """Predicado completo: bloco contíguo e vocabulário da música ⊆ sequência."""
    return contigua(cifra, sequencia) and vocabulario_contido(cifra, sequencia)
