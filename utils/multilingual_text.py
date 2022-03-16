# -*- coding: utf-8 -*-
import langid
import re
from pykakasi import kakasi
from utils.text import to_pinyin,_phonemize,_phonemize_zh


def remove_punctuation(text):
    """Remove punctuation from text."""
    punctuations_out = '、。，：？！（）"(),.:;¿?¡!\\'    # punctuation which usualy occurs outside words (important during phonemization)
    punctuations_in  = '\'-'             # punctuation which can occur inside a word, so whitespaces do not have to be present
    punct_re = '[' + punctuations_out + punctuations_in +' '+ ']'
    return re.sub(punct_re.replace('-', '\-'), '', text)


def convert_kanji(text):
    kks = kakasi()
    hira_text=""
    results = kks.convert(text)
    for result in results:
        hira_text+=result['hira']
    return hira_text


def split_mul_lang(text):
    """
    Split a sentence according to their language. It supports en,zh,ko,jp.
    :param text: text
    """
    
    res_list=[]
    tmp=''
    punctuation= '、。，：？！（）"(),.:;¿?¡!\\'
    
    en_captial=[chr(i) for i in range(ord(u'A'),ord(u'Z')+1)]
    en_small=[chr(i) for i in range(ord(u'a'),ord(u'z')+1)]
    ja_kata=[chr(i) for i in range(ord(u'\u30a0'),ord(u'\u30ff')+1)]
    ja_hira=[chr(i) for i in range(ord(u'\u3040'),ord(u'\u309f')+1)]
    zh_list=[chr(i) for i in range(ord(u'\u4e00'),ord(u'\u9fa5')+1)]
    ko_list=[chr(i) for i in range(ord(u'\uac00'),ord(u'\ud7ff')+1)]
    
    en_list=en_captial+en_small 
    ja_list=ja_kata+ja_hira

    text = text.strip()    
    for idx,char in enumerate(text):
        if char in en_list:
            tmp +=char
            if idx+1<len(text)and text[idx+1] not in en_list+list(punctuation):
                res_list.append(tmp)
                tmp=''
        elif char in zh_list:
            tmp +=char
            if idx+1<len(text)and text[idx+1] not in zh_list+list(punctuation):
                res_list.append(tmp)
                tmp=''
        elif char in ko_list:
            tmp +=char
            if idx+1<len(text)and text[idx+1] not in ko_list+list(punctuation):
                res_list.append(tmp)
                tmp=''
        elif char in ja_list:
            tmp +=char

            if idx+1<len(text)and text[idx+1] not in ja_list+list(punctuation):
                res_list.append(tmp)
                tmp=''
        else:
            #识别标点前后是否为同一语言
            tmp+=char
            if idx+1<len(text)and langid.classify(text[idx+1])[0]!=langid.classify(text[idx-1])[0]:
                res_list.append(tmp)
                tmp=''
    res_list.append(tmp)
    return res_list


def mix_lang_text(input_text, lang_list, speaker_list, use_phoneme=False):
    """
    默认使用音素化。输入字符列表为原文。
    不使用音素化时则将输入字符列表直接拼接。
    :param input_text: list of text. ['hello，', '你好。'] etc.
    :param lang_list: list of language corresponding to input_text. ['en', 'zh'] etc.
    :param speaker_list: list of speaker to speak.
    :param use_phoneme: use phoneme or not.
    
    """
    output_list = []
    mix_lang=[]
    inputs = []
    if use_phoneme:
        for idx,text in enumerate(input_text):
            if lang_list[idx] == 'zh':
                output_list.append(_phonemize_zh(text))
            elif lang_list[idx]=='en':
                output_list.append(_phonemize(text,'en-us'))
            elif lang_list[idx]=='de':
                output_list.append(_phonemize(text,'de'))    
            if idx == len(lang_list)-1:
                mix_lang.append(lang_list[idx])
            else:
                mix_lang.append(lang_list[idx]+ '-' +str(len(output_list[idx])))            

        for speaker in speaker_list:
            inputs.append(' '.join(output_list)+"|"+speaker+"|"+','.join(mix_lang))
    else:
        for idx,text in enumerate(input_text):
            if lang_list[idx] == 'zh':
                text = to_pinyin(text)
            elif lang_list[idx] == 'ja':
                text = convert_kanji(text)
                
            output_list.append(text)
                
            if idx == len(lang_list)-1:
                mix_lang.append(lang_list[idx])
            else:
                mix_lang.append(lang_list[idx]+ '-' +str(len(text)))         
        for speaker in speaker_list:
            inputs.append(''.join(output_list)+"|"+speaker+"|"+','.join(mix_lang))
    return inputs


def gen_mul_manifest(text, speaker_list,use_phoneme=False):
    """
    generate the code-switching inference manifest 
    :param text: text
    :param speaker_list: list of speaker 
    
    """
    if langid.classify(text)[0]== 'ja':
        text = convert_kanji(text)
        
    split_list = split_mul_lang(text)
    lang_list=[]
    for i in split_list:
        lang = langid.classify(remove_punctuation(i))[0]
        lang_list.append(lang)
    print(split_list,lang_list,speaker_list)
    res = mix_lang_text(split_list,lang_list,speaker_list,use_phoneme)
    
    return res,split_list,lang_list
