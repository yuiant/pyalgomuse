#! /usr/bin/env python
# -*- coding: utf-8 -*-

import enum


class Segment():
    def __init__(self, xml=None, **kw):
        if xml is not None:
            self._parse_xml(xml)

        self._measures = []
        self._metadata = None

        self._num_measures = kw.get('num_measures', 0)
        self._notes = kw.get('notes')
        self._chords = kw.get('chords')

    def _parse_xml(self, xml):
        pass

    @property
    def measures(self):
        return self._measures

    @property
    def metadata(self):
        return self._metadata

    @property
    def chord_transition_matrix(self):
        return None


class Measure:
    def __init__(self):
        pass

    @property
    def melody_vector(self):
        return None

    @property
    def chords(self):
        return None

    @property
    def main_chord(self):
        return None

    @property
    def melody_distribution_in_chord(self):
        return None


class SegmentType(str, enum.Enum):
    CHORUS = 'chorus'
    INTRO = 'intro'
    VERSE = 'verse'
    INTRUMENTAL = 'instrumental'


class YmlNote:
    def __init__(self, k, v):
        self.order = int(k.split('_')[1])
        self.key = v[0]
        self.octave = v[1]
        self.delta_time = v[3]
        # if self.order == 1:
        #     self.event_on = 0

    def __repr__(self):
        return str(self.__dict__)
