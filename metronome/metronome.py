#! /usr/bin/env python

import pyaudio
import wave
import time
import argparse
import sys
import select
import termios
import os


# setup key press detection
class KeyPoller():
    def __enter__(self):
        # Save the terminal settings
        self.fd = sys.stdin.fileno()
        self.new_term = termios.tcgetattr(self.fd)
        self.old_term = termios.tcgetattr(self.fd)

        # New terminal setting unbuffered
        self.new_term[3] = (self.new_term[3] & ~termios.ICANON & ~termios.ECHO)
        termios.tcsetattr(self.fd, termios.TCSAFLUSH, self.new_term)

        return self

    def __exit__(self, type, value, traceback):
        termios.tcsetattr(self.fd, termios.TCSAFLUSH, self.old_term)

    def poll(self):
        dr, dw, de = select.select([sys.stdin], [], [], 0)
        if not dr == []:
            return sys.stdin.read(1)
        return None


class Metronome():
    def __init__(self, bpm, time_sig, accent_file, beat_file):
        self.bpm = int(bpm)
        self.time_sig = int(time_sig)
        self.accent_file = accent_file
        self.beat_file = beat_file
        self.pause_flag = False

        # Prepare sound files
        self.p = pyaudio.PyAudio()
        high = wave.open(self.accent_file, "rb")
        low = wave.open(self.beat_file, "rb")

        self.stream = self.p.open(format=self.p.get_format_from_width(high.getsampwidth()),
                                  channels=high.getnchannels(),
                                  rate=high.getframerate(),
                                  output=True)

        self.high_data = high.readframes(2048)
        self.low_data = low.readframes(2048)

        print("bpm: {}, time_sig: {}".format(self.bpm, self.time_sig))
        return None

    def change_bpm(self, direction):
        if direction == "u":
            self.bpm += 5
        else:
            self.bpm -= 5
        print("New bpm: {}".format(self.bpm))
        return None

    def change_time(self, direction):
        if direction == "r":
            self.time_sig += 1
        else:
            if self.time_sig == 1:
                print("Time signature can't be lowered")
            else:
                self.time_sig -= 1
        print("New time signature: {}".format(self.time_sig))
        return None

    def quit(self):
        self.stream.close()
        self.p.terminate()
        # print("Exiting...")
        # sys.exit(0)
        self.on_exit()

    def on_exit(self):
        print('metronome Exiting...')
        os.system('../scripts/result.sh')
        # print('exec another sh script')
        sys.exit(0)

    def pause(self):
        self.pause_flag = ~self.pause_flag
        if self.pause_flag:
            print("Paused")
        else:
            print("Started")
        return None

    def change_parser(self, chr):
        if chr == "q":
            self.quit()
        elif chr == " ":
            self.pause()
        elif chr in ["u", "d"]:
            self.change_bpm(chr)
        elif chr in ["l", "r"]:
            self.change_time(chr)
        return None

    def metronome(self):
        with KeyPoller() as key_poller:
            while True:
                for i in range(self.time_sig):
                    c = key_poller.poll()
                    self.change_parser(c)
                    if self.pause_flag:
                        continue
                    if i % self.time_sig == 0:
                        self.stream.write(self.high_data)
                    else:
                        self.stream.write(self.low_data)
                    time.sleep(60 / self.bpm)

# parse cli arguments
parser = argparse.ArgumentParser()
parser.add_argument("-b", "--bpm", default=120)
parser.add_argument("-t", "--time_sig", default=4)
args = parser.parse_args()

TIME_SIG = args.time_sig
BPM = args.bpm

m = Metronome(BPM, TIME_SIG, r"High Seiko SQ50.wav", r"Low Seiko SQ50.wav")

m.metronome()
