#! /usr/bin/env python
# -*- coding: utf-8 -*-

import json

import numpy as np

MY_CHORDS = [
    '<START>', 'C', 'D', 'E', 'F', 'G', 'A', 'B', 'cm', 'dm', 'em', 'fm', 'gm',
    'am', 'bm'
]


def generate_chords(pitch_matrix):
    A = np.load('A.npy')
    B = np.load('B.npy')

    with open('symbol2idx.json') as f:
        symbol2idx = json.load(f)

    # idx2symbol = {v: k for k, v in symbol2idx.items()}

    my_chords = MY_CHORDS if len(MY_CHORDS) > 0 else list(symbol2idx.keys())

    myidx = [symbol2idx.get(c) for c in my_chords]

    myidx2sym = dict(zip(range(len(my_chords)), my_chords))

    end_prob = A[myidx[1:], -1]
    end_prob = end_prob / end_prob.sum()

    myA = A[myidx, :][:, myidx]
    myB = B[myidx, :]

    A_normal = (myA.transpose() / myA.transpose().sum(axis=0)).transpose()

    initial_dist = A_normal[0, 1:].reshape(1, -1)
    trans_prob = (A_normal[1:, 1:]).transpose()

    chord_melody_dist = (
        myB.transpose() / myB.transpose().sum(axis=0)).transpose()[1:, :]

    emissions = list(range(pitch_matrix.shape[0]))

    emission_prob = np.dot(chord_melody_dist, pitch_matrix.transpose())
    emission_prob = (emission_prob.transpose() /
                     emission_prob.transpose().sum(axis=0)).transpose()

    _init = initial_dist
    ret = []
    for i in range(len(emissions)):
        if i == 0:
            _init = emission_prob[:, 0] * initial_dist

        else:
            _init = np.dot(trans_prob, _init.reshape(-1, 1)).reshape(
                1, -1) * emission_prob[:, i]

            if i == len(emissions) - 1:
                _init = _init.reshape(1, -1) * end_prob
        _init = _init.reshape(1, -1)
        ret.append(_init)

    output = [r.argmax() for r in ret]

    output_chords = [myidx2sym.get(o + 1) for o in output]

    return output_chords
