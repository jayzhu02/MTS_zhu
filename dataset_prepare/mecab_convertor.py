#encoding=utf-8

import fileinput
import romkan
import MeCab

wakati = MeCab.Tagger("-O wakati")
yomi = MeCab.Tagger("-O yomi")

wakati.parse("pythonが大好きです")

yomi.parse(wakati.parse("pythonが大好きです")).split()

romkan.to_roma(yomi.parse(wakati.parse("pythonが大好きです"))).split()

for s in fileinput.input():
    print(romkan.to_roma(yomi.parse(wakati.parse(s))))
