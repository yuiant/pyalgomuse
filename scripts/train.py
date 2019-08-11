#! /usr/bin/env python
# -*- coding: utf-8 -*-

import copy
import glob
import os

import iteration_utilities
import numpy as np
import pandas as pd
from pyalgomuse.model import Segment
from pyalgomuse.utils.theorytab.roman_to_symbol import (chord_parser,
                                                        note_parser)
from pyalgomuse.utils.theorytab.tab_parser import proc_xml

import tqdm
import itertools

import multiprocessing as mp
import functools
import json
import re

XML_ROOT = '../datasets/hooktheory_dataset/datasets/xml'
FILE_SUFFIX = '*.xml'


def get_info(xd):
    def _segment_parser(sg):
        num_measures = sg['numMeasures']
        notes = sg['melody']['voice'][0]['notes']['note']
        chords = sg['harmony']['chord']

        return Segment(num_measures=num_measures, notes=notes, chords=chords)

    segments = xd['data']['segment']
    segment = segments if hasattr(segments, 'keys') else segments[0]

    return _segment_parser(segment)


def stats_value(infos, filed, note=True):
    if note:
        ret = [[n.get(filed) for n in s._notes if not isinstance(n, str)]
               for s in infos]
    else:
        ret = [[c.get(filed) for c in s._chords if not isinstance(c, str)]
               for s in infos]

    flatten = list(iteration_utilities.flatten(ret))
    return flatten


def handle_segment(segment, symbol2idx):
    pitch_count = 12
    a = np.zeros([len(symbol2idx), len(symbol2idx)])
    b = np.zeros([len(symbol2idx), pitch_count])

    try:

        sg = copy.deepcopy(segment)
        notes = [n for n in sg['notes'] if n]
        chords = [h for h in sg['chords'] if h]

        new_notes = []

        notes = sorted(notes, key=lambda x: x['event_on'])
        chords = sorted(chords, key=lambda x: x['event_on'])

        for n in notes:
            for i, c in enumerate(chords):
                if n['event_on'] >= c['event_on'] and n['event_on'] < c['event_off']:
                    # note is not overlap on chord
                    if n['event_off'] <= c['event_off']:
                        n.update(idx=i)
                        break
                    else:
                        _n = copy.deepcopy(n)
                        _n['event_off'] = c['event_off']
                        _n.update(idx=i)
                        n['event_on'] = c['event_off']
                        new_notes.append(_n)

        notes.extend(new_notes)
        notes = sorted(notes, key=lambda x: x['event_on'])

        df = pd.DataFrame(notes)
        df = df.dropna()
        df['event_duration'] = df['event_off'] - df['event_on']
        df['pitch'] = df['pitch'].map(_normalize_pitch)
        chords = [_normalize_chord_symbol(c['symbol']) for c in chords]
        df['chord'] = df['idx'].map(lambda x: int(symbol2idx[chords[int(x)]]))


        distrubition = df[['chord', 'pitch', 'event_duration']].groupby(
            ['chord', 'pitch']).sum().reset_index()

        chords = ['<START>'] + chords + ['<EOF>']

        idx = [symbol2idx[c] for c in chords]

        a[idx[0:-1], idx[1:]] = 1
        b[distrubition['chord'], distrubition['pitch']] = distrubition[
            'event_duration']
    except Exception as e:
        pass

    return a, b


def _normalize_chord_symbol(symbol):
    return symbol.encode('ascii', 'ignore').decode('ascii').split(' ')[0]


def _normalize_pitch(pitch):
    return int(pitch % 12)


def get_all_pitch_and_symbol(segements, raw=False):
    pitches = [[n['pitch'] for n in s['notes'] if n] for s in segements]
    pitches = list(iteration_utilities.flatten(pitches))

    symbols = [[c['symbol'] for c in s['chords'] if c] for s in segements]
    symbols = list(iteration_utilities.flatten(symbols))

    if not raw:
        pitches = [_normalize_pitch(p) for p in pitches]
        symbols = [_normalize_chord_symbol(s) for s in symbols]

    return pitches, symbols


def parse_xml_file(xml_file):
    try:
        data = proc_xml(xml_file)
        mode = data.get('metadata').get('mode', '1')
        melody = data.get('tracks').get('melody')
        chord = data.get('tracks').get('chord')
        notes = [note_parser(n, mode) for n in melody]
        df_notes = pd.DataFrame([_n for _n in notes if _n])

        best_offsets = estimate_best_offset_by_chords(chord, mode)
        # best_offsets = list(range(12))

        best_offset = estimate_best_offset_by_notes(df_notes, best_offsets)[0]
        chords = [chord_parser(c, mode, best_offset) for c in chord]
        notes = [note_parser(n,mode,best_offset) for n in melody]
        data.update({'notes': notes, 'chords': chords})
        data.update(fp=xml_file)
        data.update(offset=best_offset)

        return data

    except Exception as e:
        # pass
        print(e)


def b_value(chords, mode, offset):
    _chords = [chord_parser(c, mode, offset) for c in chords if c]
    symbols = [c['symbol'] for c in _chords if c]
    contain_b = [re.match(r'\wb\w*', s) for s in symbols]

    b_value = len([cb for cb in contain_b if cb]) / len(contain_b)
    return b_value


def b_value_by_notes(df_note, offset):
    semi = {
        0: False,
        1: True,
        2: False,
        3: True,
        4: False,
        5: False,
        6: True,
        7: False,
        8: True,
        9: False,
        10: True,
        11: False
    }

    df = copy.deepcopy(df_note)
    df['semi'] = df['pitch'].map(lambda x: semi.get((x + offset) % 12))
    df = df[['semi', 'event_duration']].groupby('semi').sum()
    df = df['event_duration'] / df['event_duration'].sum()
    if True in df.index:
        return df.loc[True]
    else:
        return 0


def estimate_best_offset_by_chords(chords, mode):

    b_values = np.array(
        [b_value(chords, mode, offset) for offset in range(12)])
    best_offsets = [i for i, bv in enumerate(b_values) if bv == min(b_values)]
    return best_offsets


def estimate_best_offset_by_notes(df_notes, offsets):
    if len(offsets) == 1:
        return [offsets[0]]

    else:
        b_values = [
            b_value_by_notes(df_notes, offset) for offset in offsets
        ]
        b_values = np.array(b_values)
        best = [offsets[i] for i,bv in enumerate(b_values) if bv == min(b_values)]
        best_offsets = best
        return best_offsets


def main(core=6):
    files = glob.glob(
        os.path.join(XML_ROOT, '**', FILE_SUFFIX), recursive=True)


    ret = []
    error = []
    error1 = []

    print('parsing...')

    with mp.Pool(core) as p:
        ret = p.map(parse_xml_file, tqdm.tqdm(files))

    error = [i for i,r in enumerate(ret) if r is None]
    ret = [r for r in ret if r]


    print('normal:', len(ret))
    print('error:', len(error))

    pitches, symbols = get_all_pitch_and_symbol(ret)
    # return ret, symbols

    print('pitch count:', len(set(pitches)))
    print('symbol count:', len(set(symbols)))

    unique_symbols = list(set(symbols))
    unique_symbols = ['<START>'] + unique_symbols + ['<EOF>']
    symbol2idx = dict(zip(unique_symbols, range(len(unique_symbols))))
    # idx2symbol = {v:k for k,v in symbol2idx.items()}

    A = np.zeros([len(symbol2idx), len(symbol2idx)])
    # <EOF> status
    A[-1, -1] = 1
    B = np.ones([len(symbol2idx), 12]) * 1e-4

    print('calculating...')

    _handle_segment = functools.partial(handle_segment, symbol2idx=symbol2idx)

    with mp.Pool(core) as p:
        M = p.map(_handle_segment, tqdm.tqdm(ret))

    M = [m for m in M if m]

    As = [m[0] for m in M]
    Bs = [m[1] for m in M]

    A += sum(As)
    B += sum(Bs)

    # save
    print('saving...')
    with open('symbol2idx.json', 'w') as f:
        json.dump(symbol2idx, f)

    np.save('A.npy', A)
    np.save('B.npy', B)

    return A, B, symbol2idx

def analyse(data):
    print('file:',data['fp'])
    print('best offset:',data['offset'])
    print('chord seq:',get_chord_seq(data))
    print('pitch seq:',get_pitch_seq(data))

    pitch2note = {v:k for k,v in NOTES_MAP.items()}
    print('note seq:',[pitch2note.get(p) for p in get_pitch_seq(data)])


NOTES = ['C','Db','D','Eb','E','F','Gb','G','Ab','A','Bb','B']
NOTES_MAP = dict(zip(NOTES,range(12)))


def get_by_pitch(data,note):
    ret = [d for d in data if NOTES_MAP.get(note) in get_pitch_seq(d)]
    return ret

def get_by_chord(data,chord):
    ret = [d for d in data if chord in get_chord_seq(d)]
    return ret

def get_by_condition(data,chord = None,note = None):
    if chord is None and note is not None:
        return get_by_pitch(data,note)

    elif chord is not None and note is None:
        return get_by_chord(data,chord)

    elif chord is not None and note is not None:
        ret = [d for d in data if NOTES_MAP.get(note) in get_pitch_seq(d)
               and chord in get_chord_seq(d)]

        return ret

    else:
        raise Exception('chord and note can not be None at the same time')


def get_pitch_seq(data):
    pitches = [n['pitch']%12 for n in data['notes'] if n]
    return pitches

def get_chord_seq(data):
    chords = [_normalize_chord_symbol(c['symbol']) for c in data['chords'] if c]
    return chords

if __name__ == '__main__':
    core = 6

    files = glob.glob(
        os.path.join(XML_ROOT, '**', FILE_SUFFIX), recursive=True)

    ret = []
    error = []
    error1 = []

    print('parsing...')

    with mp.Pool(core) as p:
        ret = p.map(parse_xml_file, tqdm.tqdm(files))

    error = [i for i,r in enumerate(ret) if r is None]
    ret = [r for r in ret if r]


    print('normal:', len(ret))
    print('error:', len(error))

    pitches, symbols = get_all_pitch_and_symbol(ret)
    # return ret, symbols

    print('pitch count:', len(set(pitches)))
    print('symbol count:', len(set(symbols)))

    unique_symbols = list(set(symbols))
    unique_symbols = ['<START>'] + unique_symbols + ['<EOF>']
    symbol2idx = dict(zip(unique_symbols, range(len(unique_symbols))))

    A = np.zeros([len(symbol2idx), len(symbol2idx)])
    # <EOF> status
    A[-1, -1] = 1
    B = np.ones([len(symbol2idx), 12]) * 1e-4

    print('calculating...')

    _handle_segment = functools.partial(handle_segment, symbol2idx=symbol2idx)

    with mp.Pool(core) as p:
        M = p.map(_handle_segment, tqdm.tqdm(ret))

    M = [m for m in M if m]

    As = [m[0] for m in M]
    Bs = [m[1] for m in M]

    A += sum(As)
    B += sum(Bs)

    # save
    print('saving...')
    with open('symbol2idx.json', 'w') as f:
        json.dump(symbol2idx, f)

    np.save('A.npy', A)
    np.save('B.npy', B)


