# coding: utf-8
"""Demonstra a dependência de ordem do endpoint /similares em relação ao hash seed.

Reproduz a construção de main.py:49-98 (generos como set -> list, genero_musicas
ordenado por popularidade, musicas como OrderedDict) e imprime os primeiros IDs
da primeira página de cada sequência. Rode duas vezes:

    PYTHONHASHSEED=0 python3 research/scripts/ordem_endpoint.py
    PYTHONHASHSEED=1 python3 research/scripts/ordem_endpoint.py

O conjunto total é o mesmo; a ordem dos blocos de gênero (e portanto o conteúdo
da primeira página) muda.
"""
from __future__ import print_function

import collections

ARTISTA_ID, MUSICA_ID, ARTISTA, MUSICA, GENERO, POPULARIDADE, TOM, SEQ_FAMOSA, CIFRA = range(9)
TAM_PAGINA = 100


def limpa_cifra(raw_cifra):
    cifra = []
    for m in raw_cifra:
        if m.strip() != '':
            if '|' in m:
                cifra.append(m.split('|')[0].split()[0])
            else:
                cifra += m.split()
    return cifra


def main():
    musicas_dict = {}
    genero_musicas = {}
    generos = set()
    acordes_global = set()

    with open('data/top/dataset_final.csv') as f:
        f.readline()
        for line in f:
            line = line.replace('"', '').replace('NA', '')[:-1]
            m = line.split(',')
            if len(m) < 9:
                continue
            cifra = limpa_cifra(m[CIFRA].split(';')) if m[CIFRA] != '' else []
            seqs = m[SEQ_FAMOSA].split(';')
            obj = {
                'id': m[ARTISTA_ID] + '_' + m[MUSICA_ID],
                'genero': m[GENERO],
                'popularidade': int(m[POPULARIDADE].replace('.', '')),
                'seqs': seqs,
                'acordes': list(set(cifra)),
            }
            musicas_dict[obj['id']] = obj
            generos.add(obj['genero'])
            genero_musicas.setdefault(obj['genero'], []).append(obj)
            acordes_global.update(obj['acordes'])

    musicas = collections.OrderedDict(sorted(musicas_dict.items(),
                                             key=lambda x: x[1]['popularidade'], reverse=True))
    generos = list(generos)
    for k in genero_musicas:
        genero_musicas[k].sort(key=lambda x: x['popularidade'], reverse=True)

    collection = []
    for g in generos:
        collection += genero_musicas[g]

    print('hash seed:', __import__('os').environ.get('PYTHONHASHSEED'))
    print('generos[:8]:', generos[:8])
    print('acordes[:8]:', list(acordes_global)[:8])
    for idx, key in enumerate(['BmGDA', 'CGAmF', 'EmG', 'CA7DmG7', 'GmF', 'CC7FFm']):
        tagged = [m for m in collection if str(idx) in m['seqs']]
        page1 = tagged[:TAM_PAGINA]
        print('{}: total={} page1={} first5={}'.format(
            key, len(tagged), len(page1), [m['id'] for m in page1[:5]]))


if __name__ == '__main__':
    main()
