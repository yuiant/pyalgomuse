#! /bin/sh

BASEPATH=$(cd `dirname $0`; pwd)
RECORD_FILE=$BASEPATH/saved/record.yml
BT_FILE=$BASEPATH/saved/bt.toml

if [ -f "${RECORD_FILE}" ];then
rm $RECORD_FILE
echo 'OLD RECORD DELETED!'
fi
echo 'input bpm:'
read bpm
echo 'input time_sig:'
read sig

echo "bpm = ${bpm}\ntime_sig = ${sig}" > $BT_FILE
gnome-terminal -- bash -c "sh ./record.sh";exec bash &
cd ../metronome/&&./metronome.py -b $bpm -t $sig


