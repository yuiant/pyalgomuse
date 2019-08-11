#! /bin/sh

echo 'continue to generate chords?(y/n)'

read option

cd `dirname $0`

if [ "$option"x = "y"x ];then
python3 ./run.py
timidity ./saved/record.mid
fi
