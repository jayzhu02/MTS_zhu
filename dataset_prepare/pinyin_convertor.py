#encoding=utf-8

import fileinput
import pinyin
import jieba
import sys
sys.path.append('../')
from utils.text import _phonemize

s="今天天气真好。"
text = ' '.join([pinyin.get(x) for x in jieba.cut(s.rstrip())])
print(_phonemize(text,True,'cmn'))

for s in fileinput.input():
    print(' '.join([pinyin.get(x) for x in jieba.cut(s.rstrip())]))
