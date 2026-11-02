# coding: utf-8
"""Medições descritivas do CSV e do carregamento em memória (pergunta 1).

Uso (a partir da raiz do repositório):

    PYTHONHASHSEED=0 python3 research/scripts/medicoes_dados.py

Lê o CSV exatamente como main.py:49-98 (incluindo o replace('NA','') e o
descarte da primeira linha) e imprime contagens usadas no documento.
"""
from __future__ import print_function

import collections
import re

ARTISTA_ID, MUSICA_ID, ARTISTA, MUSICA, GENERO, POPULARIDADE, TOM, SEQ_FAMOSA, CIFRA = range(9)


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


def parse_line(line):
    """main.py:52-63 (line já sem o '\\n')"""
    line = line.replace('"', '').replace('NA', '')
    m = line.split(',')
    if len(m) < 9:
        return None
    raw = [x for x in m[CIFRA].split(';')] if m[CIFRA] else []
    return m, raw, limpa_cifra(raw)


def main():
    total_lines = 0
    first_line = None
    rows = []
    with open('data/top/dataset_final.csv') as f:
        for line in f:
            total_lines += 1
            line = line[:-1] if line.endswith('\n') else line
            if first_line is None:
                first_line = line
            parsed = parse_line(line)
            if parsed is None:
                continue
            rows.append(parsed)

    # main.py:50 descarta a primeira linha
    rows = rows[1:]

    with_cifra = [r for r in rows if r[1]]
    empty_cifra = [r for r in rows if not r[1]]
    tokens = collections.Counter()
    for _, _, clean in rows:
        tokens.update(clean)

    groups = collections.defaultdict(set)
    for t in tokens:
        groups[t.lower()].add(t)
    collisions = {k: v for k, v in groups.items() if len(v) > 1}
    mm = {k: v for k, v in collisions.items()
          if any('M' in t for t in v) and any('m' in t for t in v)}
    collision_tokens = set()
    for v in collisions.values():
        collision_tokens |= v
    mm_tokens = set()
    for v in mm.values():
        mm_tokens |= v
    songs_with_collision = sum(1 for _, _, clean in rows if any(t in collision_tokens for t in clean))
    songs_with_mm = sum(1 for _, _, clean in rows if any(t in mm_tokens for t in clean))

    repeated = sum(1 for _, _, clean in rows if len(clean) != len(set(clean)))
    repeated_raw = sum(1 for _, raw, _ in rows
                       if len([x for x in raw if x.strip() != '']) !=
                       len(set(x for x in raw if x.strip() != '')))
    changed_incl_empty = sum(1 for _, raw, clean in rows if raw != clean)
    changed = sum(1 for _, raw, clean in rows
                  if [x for x in raw if x.strip() != ''] != clean)
    any_pipe = sum(1 for _, raw, _ in rows if any('|' in x for x in raw))

    rb = sum(1 for m, _, _ in rows if m[GENERO] == 'R&B;')

    # títulos alterados pelo replace('NA','') global (main.py:53)
    na_changed = []
    for line in open('data/top/dataset_final.csv'):
        line = line[:-1] if line.endswith('\n') else line
        orig = line.replace('"', '').split(',')
        if len(orig) < 9:
            continue
        parsed = parse_line(line)
        if parsed is None:
            continue
        if orig[MUSICA] != parsed[0][MUSICA]:
            na_changed.append((orig[MUSICA], parsed[0][MUSICA]))

    print('linhas no arquivo:', total_lines)
    print('linhas carregadas (main.py descarta a 1a):', len(rows))
    print('primeira linha (descartada):', first_line.split(',')[0] + '_' + first_line.split(',')[1])
    print('músicas com cifra:', len(with_cifra))
    print('músicas com cifra vazia:', len(empty_cifra))
    print('tokens limpos distintos:', len(tokens))
    print('grupos de colisão case-insensitive:', len(collisions))
    print('grupos de colisão com M/m:', len(mm))
    print('músicas que contêm algum token em colisão (todos os grupos):', songs_with_collision)
    print('músicas que contêm algum token em colisão M/m:', songs_with_mm)
    print('músicas com token repetido na cifra limpa:', repeated)
    print('músicas com token repetido na lista bruta não vazia:', repeated_raw)
    print('músicas em que a lista bruta difere da limpa (incluindo vazios):', changed_incl_empty)
    print('músicas em que a lista bruta não vazia difere da limpa:', changed)
    print('músicas com tablatura (|) na cifra:', any_pipe)
    print('linhas com gênero R&B;:', rb)
    print('títulos alterados por replace(NA):', len(na_changed))
    for a, b in na_changed:
        print('  {!r} -> {!r}'.format(a, b))
    print()
    print('exemplos de grupos de colisão:')
    for k in sorted(collisions)[:12]:
        print('  {} -> {}'.format(k, sorted(collisions[k])))
    print()
    print('exemplo de repetição (Marajá):')
    for m, raw, clean in rows:
        if 'Maraj' in m[MUSICA]:
            print('  {} | cifra={} | tag={}'.format(m[MUSICA], ';'.join(clean)[:120], m[SEQ_FAMOSA]))
            break


if __name__ == '__main__':
    main()
