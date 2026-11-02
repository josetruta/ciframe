# coding: utf-8
"""Validação empírica do matching de sequências (pergunta 2 de 01-research.md).

Lê data/top/dataset_final.csv do mesmo jeito que main.py (linhas 49-98),
reproduz get_famosas() de scripts/generate_data_set.py (linhas 7-24) e compara
o conjunto de músicas marcadas com o que cada interpretação de "a sequência
aparece na música" produz.

Uso (a partir da raiz do repositório):

    PYTHONHASHSEED=0 python3 research/scripts/validar_sequencias.py

Não depende de Flask; só da biblioteca padrão.
"""
from __future__ import print_function

import collections
import math

ARTISTA_ID, MUSICA_ID, ARTISTA, MUSICA, GENERO, POPULARIDADE, TOM, SEQ_FAMOSA, CIFRA = range(9)

# main.py:40-45
SEQUENCIAS = collections.OrderedDict([
    ('BmGDA', ['Bm', 'G', 'D', 'A']),
    ('CGAmF', ['C', 'G', 'Am', 'F']),
    ('EmG', ['Em', 'G']),
    ('CA7DmG7', ['C', 'A7', 'Dm', 'G7']),
    ('GmF', ['Gm', 'F']),
    ('CC7FFm', ['C', 'C7', 'F', 'Fm']),
])


def limpa_cifra(raw_cifra):
    """main.py:11-23"""
    cifra = []
    for m in raw_cifra:
        if m.strip() != '':
            if '|' in m:
                cifra.append(m.split('|')[0].split()[0])
            else:
                cifra += m.split()
    return cifra


def carrega():
    """main.py:49-98 (sem construir objetos Musica)."""
    rows = []
    with open('data/top/dataset_final.csv') as f:
        f.readline()  # main.py:50 descarta a primeira linha (não há cabeçalho)
        for line in f:
            line = line.replace('"', '').replace('NA', '')[:-1]
            m = line.split(',')
            if len(m) < 9:
                continue
            raw = [x for x in m[CIFRA].split(';')] if m[CIFRA] else []
            rows.append({
                'id': m[ARTISTA_ID] + '_' + m[MUSICA_ID],
                'nome': m[MUSICA],
                'genero': m[GENERO],
                'raw': [x for x in raw if x.strip() != ''],
                'clean': limpa_cifra(raw),
                'tag': [x for x in m[SEQ_FAMOSA].split(';') if x != ''],
            })
    return rows


def get_famosas(acorde):
    """scripts/generate_data_set.py:7-24, literal."""
    seqs = ['bm;g;d;a', 'c;g;am;f', 'em;g', 'c;a7;dm;g7', 'gm;f', 'c;c7;f;fm']
    out = []
    for i in range(len(seqs)):
        s = seqs[i]
        acorde = acorde.lower()
        if s in acorde:
            achou = True
            for l in acorde.split(';'):
                tokens = s.split(';')
                if l not in tokens:
                    achou = False
                    break
            if achou:
                out.append(str(i))
    return out


def contigua(cifra, seq, case_insensitive=True):
    a = [c.lower() for c in cifra] if case_insensitive else list(cifra)
    b = [c.lower() for c in seq] if case_insensitive else list(seq)
    n = len(b)
    if n == 0 or n > len(a):
        return False
    return any(a[i:i + n] == b for i in range(len(a) - n + 1))


def subseq_ordenada(cifra, seq, case_insensitive=True):
    a = [c.lower() for c in cifra] if case_insensitive else list(cifra)
    b = [c.lower() for c in seq] if case_insensitive else list(seq)
    it = iter(a)
    return all(any(x == y for x in it) for y in b)


def vocabulario_da_musica_contido_na_sequencia(cifra, seq, case_insensitive=True):
    """música ⊆ sequência: nenhum acorde da música fora da sequência."""
    a = {c.lower() for c in cifra} if case_insensitive else set(cifra)
    b = {c.lower() for c in seq} if case_insensitive else set(seq)
    return a <= b


def tem_intersecao(cifra, seq, case_insensitive=True):
    a = {c.lower() for c in cifra} if case_insensitive else set(cifra)
    b = {c.lower() for c in seq} if case_insensitive else set(seq)
    return bool(a & b)


def main():
    rows = carrega()
    print('linhas carregadas (main.py descarta a 1a):', len(rows))
    print('músicas com tag não vazia:', sum(1 for r in rows if r['tag']))
    print('distribuição das tags:', collections.Counter(tuple(r['tag']) for r in rows).most_common())
    print()

    print('seq | tag | get_famosas | igual? | contígua | subseq | subconj | intersec | mesmo_vocab | mesmo_vocab_sem_tag | contígua_sem_tag')
    print('-' * 130)

    total_tag = 0
    for idx, (key, seq) in enumerate(SEQUENCIAS.items()):
        tagged = {r['id'] for r in rows if str(idx) in r['tag']}
        hist = {r['id'] for r in rows if str(idx) in get_famosas(';'.join(r['raw']))}
        cont = {r['id'] for r in rows if contigua(r['clean'], seq)}
        sub = {r['id'] for r in rows if subseq_ordenada(r['clean'], seq)}
        subset = {r['id'] for r in rows if vocabulario_da_musica_contido_na_sequencia(r['clean'], seq)}
        inter = {r['id'] for r in rows if tem_intersecao(r['clean'], seq)}
        vocab = {r['id'] for r in rows if {c.lower() for c in r['clean']} == {c.lower() for c in seq}}
        total_tag += len(tagged)
        print('{} | {} | {} | {} | {} | {} | {} | {} | {} | {} | {}'.format(
            key, len(tagged), len(hist), 'SIM' if tagged == hist else 'NÃO',
            len(cont), len(sub), len(subset), len(inter), len(vocab),
            len(vocab - tagged), len(cont - tagged)))
        assert tagged == hist, 'get_famosas não reproduziu a tag para ' + key
        assert tagged == (cont & subset), 'contígua & subconjunto não reproduziu a tag para ' + key
        assert not (tagged - cont), 'tag fora de contígua para ' + key

    print()
    print('total de músicas marcadas (soma das 6):', total_tag)
    print('páginas de 100 necessárias:', {k: int(math.ceil(len([r for r in rows if str(i) in r['tag']]) / 100.0))
                                          for i, k in enumerate(SEQUENCIAS)})

    print()
    print('exemplos de mesmo vocabulário sem tag (ordem diferente):')
    for idx, (key, seq) in enumerate(SEQUENCIAS.items()):
        vocab = [r for r in rows if {c.lower() for c in r['clean']} == {c.lower() for c in seq} and str(idx) not in r['tag']]
        if vocab:
            r = vocab[0]
            print('  seq {}: {} | {}'.format(key, r['nome'], ';'.join(r['clean'])[:110]))


if __name__ == '__main__':
    main()
