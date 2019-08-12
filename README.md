# Pyalgomuse

## Description

Praitice in AI × music in python

## Installation
```
(get into your virtualenv)
cd pyalgomuse
python3 setup.py develop
pip3 install -r requirements.txt

```

## Dependency

- **TheoryTab Leadsheet Dataset**
Thanks for one of the MuseGan's authors,he has done a lot of parsing work on TheoryTab dataset.I fork and modify his [source code](https://github.com/wayne391/lead-sheet-dataset) into ***pyalgomuse/utils/theorytab*** module

- **piano-rs**
[A rust based program](https://github.com/ritiek/piano-rs) for playing virtual piano by computer keyboards in terminal.I use it for melody input.

## Task Contents

### 0.Basic Dataset Construction
- There is little Chinese/Asian songs in current public datasets.
- Lack of systemic tags in current datasets.


- [UNDER CONSTRUCTION]

### 1. Automatic Arrangement
To generate corresponding chords for the given melody

#### 1.1 Chord Symbol Generation For Melody

##### Traditional HMM based method
- training:
(The folder has already had trained results included,this step can be skipped)

```
put the <hooktheory_dataset> folder into a folder named datasets in root directory

cd scripts
python3 train.py
(the trained results store in A.npy,B.npy,symbol2idx.json)

```


- fitting:

[see a demo video](https://youtu.be/y50ilgE-c_Q)

```
cd scripts
(set your piano-rs path to $PRS Variable in record.sh)
./run_aa.sh

--- running steps ---
1.input your params of metronome,e.g. bpm & time_signature
2.play your melody on the active terminal with piano-rs,pay attention to follow the metronome.Press <Esc> to finish.
3.press <q> to quit the metronome.
4.press <y> to continue to listen the midi combination of the generated chords (column chord for simple playing) 
and your melody input(1 octave higher than your actual input)
```


##### DeepLearning basd method
- [UNDER CONSTRUCTION]


#### 1.2 Multi Instrumental Arrangement Generation
- [UNDER CONSTRUCTION]


