# -*- coding: utf-8 -*-
import re 
import string 

from phonemizer.separator import Separator
from phonemizer.phonemize import phonemize
import epitran
from params.params import Params as hp
from utils.logging import Logger
import jieba,pinyin
from time import sleep
from pykakasi import kakasi
from pypinyin import lazy_pinyin, Style, slug
import json
import soundfile as sf


_pad = '_'    # a dummy character for padding sequences to align text in batches to the same length
_eos = '~'    # character which marks the end of a sequnce, further characters are invalid
_unk = '@'    # symbols which are not in hp.characters and are present are substituted by this


def _phonemize_zh(text):
    """
    This method is only used to transfer Chinese words into ipa texts with tune number. 
    etc. 你好->ni3 hao3->ni3 xɑu3(phonemize)
    2021.1.15 Updated by Jayzhu.
    
    :param text: Chinese sentence.
    """
    num = "1234"
    tune = []
    output=sentence =''
    words = lazy_pinyin(text,style=Style.TONE3)
    
    for word in words:
        if word[-1] in num:
            sentence+= word[:-1] + ' '
            tune.append(word[-1])
        else:         
            sentence+= word + ' '
            tune.append('0')
    sentence_ipa = _phonemize(sentence,'cmn')
    for idx,word in enumerate(sentence_ipa.split()):
        if tune[idx] == '0':
            output += word + ' '
        else:
            output += word + tune[idx] + ' '    
    return output.strip()


def create_manifest(text,audio_filepath):
    """
    Create a manifest json file summarizing the data set, with each line
    containing the meta data (i.e. audio filepath, transcription text, audio
    duration) of each audio file within the data set.
    """
#     print("Creating manifest %s ..." % manifest_path)
#     json_lines = [] 
    audio_data, samplerate = sf.read(audio_filepath)
    duration = float(len(audio_data)) / samplerate
    data = json.dumps({
            'audio_filepath': audio_filepath,
            'duration': duration,
            'text': text
        },ensure_ascii=False)
#     json_lines.append(data)
    return data


def to_pinyin(text, punctuation="!:;,-.?，。！？｡：；、",style='Style.TONE'):
    re_punctuation =r'\s+([{}])'.format(punctuation)
    tt=[]
    for tx in jieba.cut(text):
        tt.append(slug(tx, style= eval(style), separator=''))
    te = ' '.join(tt)
    text = re.sub(re_punctuation, r'\1', te)
    return text


def convert_kanji(text):
    kks = kakasi()
    hira_text=""
    results = kks.convert(text)
    for result in results:
        hira_text+=result['hira']+' '
    return hira_text


def _other_symbols():
    return [_pad, _eos, _unk] + list(hp.punctuations_in) + list(hp.punctuations_out)


def build_phoneme_dicts(text_lang_pairs):
    """Create dictionaries (possibly more languages) of words (from a list of texts) with IPA equivalents."""
    dictionaries = {}
    Logger.progress(0 /len(text_lang_pairs), prefix='Building phoneme dictionary:')
    for i, (t, l) in enumerate(text_lang_pairs):
        if not (l in dictionaries):
            dictionaries[l] = {}
        if l == 'cmn':
            clear_words = jieba.lcut(remove_punctuation(t))            
        else: clear_words = remove_punctuation(t).split()
            
        for w in clear_words:
            if w in dictionaries[l]: continue
            dictionaries[l][w] = _phonemize(w, False, l).replace(' ','')
        Logger.progress((i+1) / len(text_lang_pairs), prefix='Building phoneme dictionary:')
    return dictionaries 


# +
def to_phoneme(text, preserve_punctuation, language, phoneme_dictionary=None):
    """Convert graphemes of the utterance without new line to phonemes.
    
    Arguments:
        text (string): The text to be translated into IPA.
        preserve_punctuation (bool): Set to True if the punctuation should be preserved.
        language (default hp.language): language code (e.g. en-us)
    Keyword argumnets:
        phoneme_dictionary (default None): A language specific dictionary of words with IPA equivalents, 
            used to speed up the translation which preserves punctuation (because the used phonemizer
            cannot handle punctuation properly, so we need to do it word by word).
    """
    
    phonemes = []
    text_phonemes = ""
    clear_text = remove_punctuation(text)
    if not preserve_punctuation: 
        return _phonemize(clear_text, False, language)
    
    if not phoneme_dictionary: phoneme_dictionary = {}
        
    # phonemize words of the input text
    if language == 'cmn':
        clear_words = jieba.lcut(text)
        for w in clear_words:
            phoneme = phoneme_dictionary[w] if w in phoneme_dictionary else _phonemize(w, preserve_punctuation, language).replace(' ','')    
            text_phonemes += phoneme + ' '
        return text_phonemes.strip()
    
    else: 
        text_phonemes = _phonemize(text, preserve_punctuation, language)
        return text_phonemes
    
#         clear_words = clear_text.split()
          
#     for w in clear_words:
#         phonemes.append(phoneme_dictionary[w] if w in phoneme_dictionary else _phonemize(w, language))
    
#     # add punctuation to match the punctuation in the input 
#     in_word = False
#     punctuation_seen = False
#     text_phonemes = ""
#     clear_offset = word_idx = 0
#     for idx, char in enumerate(text):
#         # encountered non-punctuation char
#         if idx - clear_offset < len(clear_text) and char in clear_text:
#             text_phonemes += phonemes[word_idx]+' '
#             word_idx += 1 
#             punctuation_seen = False           
            
#         # this should be punctuation
#         else:
#             clear_offset += 1
#             if in_word and char in hp.punctuations_in: continue
#             text_phonemes += char
#             punctuation_seen = True


# -

def _phonemize(text, language,preserve_punctuation=True):
    try:       
        seperators = Separator(word=' ', phone='')
        if language=='ja':
            text = convert_kanji(text)
        phonemes = phonemize(text, separator=seperators, backend='espeak', language=language,
                             preserve_punctuation=preserve_punctuation, language_switch='remove-flags')         
        
    except RuntimeError:        
        if language == 'cmn': language='cmn-Hans'
        # cedict_file path must be absolute path
        epi = epitran.Epitran(language,cedict_file='/data/jerik/MTS_zhu/cedict_1_0_ts_utf-8_mdbg.txt')
        phonemes = epi.transliterate(text, normpunc=True)
    phonemes.replace('\n', ' ', 1)   
#     sleep(1)
    return phonemes.strip()


def to_lower(text):
    """Convert uppercase text into lowercase."""
    return text.lower()


def remove_odd_whitespaces(text):
    """Remove multiple and trailing/leading whitespaces."""
    return ' '.join(text.split())


def remove_punctuation(text):
    """Remove punctuation from text."""
    punct_re = '[' + hp.punctuations_out + hp.punctuations_in +' '+ ']'
    return re.sub(punct_re.replace('-', '\-'), '', text)


def to_sequence(text, use_phonemes=False):
    """Converts a string of text to a sequence of IDs corresponding to the symbols in the text."""
    transform_dict = {s: i for i, s in enumerate(_other_symbols() + list(hp.phonemes if use_phonemes else hp.characters))}
    sequence = [transform_dict[_unk] if c not in transform_dict else transform_dict[c] for c in text]
    sequence.append(transform_dict[_eos])
    return sequence


def to_text(sequence, use_phonemes=False):
    """Converts a sequence of IDs back to a string"""
    transform_dict = {i: s for i, s in enumerate(_other_symbols() + list(hp.phonemes if use_phonemes else hp.characters))}
    result = ''
    for symbol_id in sequence:
        if symbol_id in transform_dict:
            s = transform_dict[symbol_id]
            if s == _eos: break
            result += s
    return result
