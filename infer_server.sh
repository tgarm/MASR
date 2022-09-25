#!/bin/bash
. ../venv/bin/activate
python server.py --pinyin_mode=True --feature_method=fbank --decoder=ctc_greedy
