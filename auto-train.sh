#!/bin/bash
python train.py --batch_size=8 --pinyin_mode=True --feature_method=fbank |tee auto-train.log

