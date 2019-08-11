#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os

import numpy as np
import pandas as pd
import pretty_midi
import pytoml
import yaml
from pychord import Chord

from pyalgomuse.common.model import YmlNote
from pyalgomuse.common.constants import NOTE_VAL_DICT, YMLNOTE_VAL_DICT, SYMBOL_CHORD_DICT
from gen_chords import generate_chords

RECORD_FILE = './saved/record.yml'
BT_FILE = 'saved/bt.toml'

MELODY_INIT_NOTE = 3 * 12
CHORD_INIT_NOTE = 4 * 12

INCOMPLETE_TOL = 0.6

MELODY_VELOCITY = 100
CHORD_VELOCITY = 80

SAVED_PATH = './saved/record.mid'


def parse_metronme(bt_file):
    with open(bt_file) as f:
        bt = pytoml.load(f)
        return bt['bpm'], bt['time_sig']


def parse_record(yml_file):
    with open(yml_file) as f:
        yml = yaml.load(f, yaml.FullLoader)
        notes = [YmlNote(k, v) for k, v in yml.items()]
        df = pd.DataFrame([n.__dict__ for n in notes])
        df = df.sort_values('order')

        return df


if __name__ == '__main__':

    bpm, time_sig = parse_metronme(BT_FILE)
    df_notes = parse_record(RECORD_FILE)

    # beat_sec = 60 / bpm
    measure_sec = 60 / bpm * time_sig

    measure_msec = measure_sec * 1000

    # divide notes into measures
    df_notes['on'] = df_notes['delta_time'].cumsum()

    on_list = sorted(list(set(df_notes['on'])))
    end_time = np.ceil(max(on_list) / measure_msec) * measure_msec
    on_list.append(end_time)

    on_off_dict = dict(zip(on_list[:-1], on_list[1:]))

    df_notes['off'] = df_notes['on'].map(lambda x: on_off_dict.get(x))

    # proc a pitch matrix
    start_measure = np.floor(on_list[0] / measure_msec)
    end_measure = np.round(end_time / measure_msec) - 1

    measure_count = end_measure - start_measure + 1

    pitch_matrix = np.zeros([int(measure_count), 12])

    for i in range(len(df_notes)):
        note = df_notes.iloc[i]

        pitch = YMLNOTE_VAL_DICT.get(note['key'])
        on = note['on']
        off = note['off']

        start = np.floor(on / measure_msec)

        while True:
            if off <= (start + 1) * measure_msec:
                pitch_matrix[int(start - start_measure), pitch] += off - on
                break

            else:
                _off = (start + 1) * measure_msec
                pitch_matrix[int(start - start_measure), pitch] += _off - on
                on = _off
                start += 1

    incomplete_start = (((start_measure + 1) * measure_msec - on_list[0]) /
                        measure_msec) < INCOMPLETE_TOL

    if incomplete_start:
        pitch_matrix = pitch_matrix[1:, :]


    # normalized
    pitch_matrix = (pitch_matrix.transpose() /
                    pitch_matrix.transpose().sum(axis=0)).transpose()

    # HMM chord generator
    chords = generate_chords(pitch_matrix)

    # transform to pychord's Chord
    chords = [SYMBOL_CHORD_DICT.get(c) for c in chords]

    # generate a midi combining melody and chord
    midi = pretty_midi.PrettyMIDI(initial_tempo=bpm)
    ts = pretty_midi.TimeSignature(time_sig, 4, 0)

    # TODO: C key default now,support key trans in future
    ks = pretty_midi.KeySignature(0, 0)

    midi.time_signature_changes.append(ts)
    midi.key_signature_changes.append(ks)

    # melody track
    melody_track = pretty_midi.Instrument(program=0)
    for i in range(len(df_notes)):
        note = df_notes.iloc[i]
        pitch = MELODY_INIT_NOTE + YMLNOTE_VAL_DICT.get(
            note['key']) + 12 * note['octave']
        _note = pretty_midi.Note(
            velocity=MELODY_VELOCITY,
            pitch=int(pitch),
            start=note['on'] / 1000,
            end=note['off'] / 1000)

        melody_track.notes.append(_note)

    # chord track
    chord_track = pretty_midi.Instrument(program=0)
    chord_start = (
        start_measure + 1
    ) * measure_sec if incomplete_start else start_measure * measure_sec

    for i, chord in enumerate(chords):
        start = chord_start + i * measure_sec
        end = start + measure_sec

        lyric = pretty_midi.Lyric(text=chord, time=start)
        midi.lyrics.append(lyric)

        previous = -1
        _chords = Chord(chord).components()
        _chords = [NOTE_VAL_DICT.get(c) for c in _chords]
        for c in _chords:
            if c < previous:
                c += 12
            note = pretty_midi.Note(
                velocity=CHORD_VELOCITY,
                pitch=int(CHORD_INIT_NOTE + c),
                start=start,
                end=end)
            previous = c
            chord_track.notes.append(note)

    midi.instruments.append(melody_track)
    midi.instruments.append(chord_track)

    # loal save
    if os.path.exists(SAVED_PATH):
        os.remove(SAVED_PATH)

    midi.write(SAVED_PATH)

    print('chords seq:','-'.join(chords))
    print('complete!!')
