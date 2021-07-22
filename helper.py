from nltk import FreqDist
from nltk.util import ngrams

import re
from collections import Counter
from itertools import repeat, chain

from flask import jsonify

# 用於 PARSE CONSTRUCTION EXTRACTOR QUERY
def parse_query(string):
    '''
    example input: "整個[傻眼:3]到[不行:3]"
    example output:
        [
             {'type': 'constant', 'word': '整個'},
             {'type': 'slot', 'word': '傻眼', 'range': '3'},
             {'type': 'constant', 'word': '到'},
             {'type': 'slot', 'word': '不行', 'range': '3'}
        ]
    '''
    results = []
    for elm in string.split('['):
        if len(elm) == 0:
            continue
        if ']' not in elm:
            results.append({'type':'constant', 'word': elm})
        else:
            for elm2 in elm.split(']'):
                if len(elm2) == 0:
                    continue
                if ':' not in elm2:
                    results.append({'type':'constant', 'word': elm2})
                else:
                    w_ = elm2.split(":")[0]
                    range_ = elm2.split(":")[1]
                    results.append({'type':'slot', 'word': w_, 'range': range_})
    return results


# 用於 PARSE CONSTRUCTION EXTRACTOR QUERY
def convert_to_regex(obj):
    '''
    example input:
        [
             {'type': 'constant', 'word': '整個'},
             {'type': 'slot', 'word': '傻眼', 'range': '3'},
             {'type': 'constant', 'word': '到'},
             {'type': 'slot', 'word': '不行', 'range': '3'}
        ]
    example output: "整個.{,3}到.{,3}"
    '''
    
    def _convert(dic):
        if dic['type'] == 'constant':
            return dic['word']
        elif dic['type'] == 'slot':
            return "(.{," + dic['range'] + "})"
        else:
            raise ValueError
    
    return ''.join(map(_convert, obj))




def get_matched_pair_from_corpus(corpus, regex_enable: bool, pattern: str, turn_type):

    re_pattern = re.compile(pattern)

    for pair in corpus:
        
        data = dict()

        # 限定出現在第一輪
        if turn_type == 'first':
            found_in_first_turn = re_pattern.search(pair['comment_content'])

            if not found_in_first_turn:
                continue

            matches = re_pattern.finditer(pair['comment_content'])
            
            data['pair'] = pair
            data['matched_iter'] = zip(repeat('first'), matches)
            yield data


        # 限定出現在第二輪
        elif turn_type == 'second':
            found_in_second_turn = re_pattern.search(pair['recomment_content'])
            
            if not found_in_second_turn:
                continue

            matches = re_pattern.finditer(pair['recomment_content'])
            
            data['pair'] = pair
            data['matched_iter'] = zip(repeat('second'), matches)
            yield data


        # 不限任何話輪
        if turn_type == 'any' or turn_type == 'both':
            
            found_in_first_turn = re_pattern.search(pair['comment_content'])
            found_in_second_turn = re_pattern.search(pair['recomment_content'])

            if turn_type == 'any':
                if not found_in_first_turn and not found_in_second_turn:
                    continue
            elif turn_type == 'both':
                if not found_in_first_turn or not found_in_second_turn:
                    continue


            if found_in_first_turn:
                matches_first = re_pattern.finditer(pair['comment_content'])

            if found_in_second_turn:
                matches_second = re_pattern.finditer(pair['recomment_content'])

            data['pair'] = pair

            iter_first = zip(repeat('first'), matches_first)
            iter_second = zip(repeat('second'), matches_second)

            data['matched_iter'] = iter_first.chain(iter_second)

            yield data

        # # 限定同時出現在兩個話輪
        # elif turn_type == 'both':
            
        #     found_in_first_turn = re_pattern.search(pair['comment_content'])
        #     found_in_second_turn = re_pattern.search(pair['recomment_content'])

        #     if not found_in_first_turn or not found_in_second_turn:
        #         continue
        

        else:
            pass


def get_pattern_position_in_a_string(string, match_obj_start, match_obj_end):
    '''
    搜尋子字串在某字串中的位置(0~1)，0代表字串首，1代表字串尾。
    實作法：使用re.Match物件的span參數來看

    string: 完整的字串
    match_obj: 
    
    return 浮點數(0~1)
    '''
    token_total = len(string[:match_obj_start]) + len(string[match_obj_end:]) + 1
    
    if token_total == 1:
        return 0

    result = (match_obj_start / token_total) * (token_total / (token_total - 1))
    
    return round(result, 2)

def get_pattern_position_in_an_utterance(string, match_obj_start, match_obj_end):
    '''
    將一個turn切分成多個utterances後，才去看match_obj的位置

    return 浮點數(0~1)
    '''
    has_only_one_utterance = True
    found = False
    len_s = len(string)
    utterances = re.compile('[。 ?？!！]').finditer(string)

    i = 0

    for delimiter in utterances:
        has_only_one_utterance = False
        delimiter_start = delimiter.start()
        delimiter_end = delimiter.end()

        
        if match_obj_end <= delimiter_start:
            found = True
            new_str = string[i:delimiter_start]
            return get_pattern_position_in_a_string(new_str, match_obj_start - i, match_obj_end - i)
        else:
            i = delimiter_end
            continue

    if has_only_one_utterance:
        return get_pattern_position_in_a_string(string, match_obj_start, match_obj_end)

    # 表示match_obj是在最後一個utterance
    if not found:
        new_str = string[i:]
        return get_pattern_position_in_a_string(new_str, match_obj_start - i, match_obj_end - i)


# def _get_pattern_position_in_a_string(string, substring):

#     l = list()

#     list_of_words_without_keyword = string.split(substring)

#     for _i, _w in enumerate(list_of_words_without_keyword):

#         l += list(_w)
        
#         if _i == len(list_of_words_without_keyword) - 1:
#             continue
        
#         else:
#             l.append(substring)


#     len_of_string = len(l)


#     if len_of_string == 1:
#         return 0

#     else:
#         r = list()

#         for i, w in enumerate(l):
#             if w == substring:
#                 r.append((i / len_of_string) * (len_of_string / (len_of_string - 1)))

#         # print(r)
#         return round(sum(r) / len(r), 2)


# def _get_pattern_position_in_an_utterance(word, content):
    
#     sentences = re.split('[。 ?？!！]', content)

#     for sentence in sentences:
#         if word in sentence:
#             try:
#                 yield get_pattern_position_in_a_string(sentence, word)
#             except:
#                 # print(sentence)
#                 # print(word)
#                 pass


def calculate_word_position_distribution(position_list, breakpoint_1, breakpoint_2):
    '''
    根據輸入的 list of position (list of floats), 以及輸入的手/中中斷點和中/末中斷點
    計算並輸出三個位置的比例
    '''
    result = {
        "initial": 0,
        "middle": 0,
        "end": 0
    }

    for position in position_list:
        if position <= breakpoint_1:
            result['initial'] += 1
        elif position >= breakpoint_2:
            result['end'] += 1
        else:
            result['middle'] += 1

    total = sum(result.values())
    if total == 0:
        return 0
    result['initial'] = round(result['initial'] / total, 2)
    result['middle'] = round(result['middle'] / total, 2) 
    result['end'] = round(result['end'] / total, 2) 

    return result

def generate_n_gram_freq_dist(content, freq_dist, n):
    grams = ngrams(content, n)
    freq_dist.update(grams)
    return freq_dist

def change_tuple_dict_key_to_str_dict_key(freq_list):
    result = []
    for ngrams, freq in freq_list:
        result.append({'ngram': '|'.join(ngrams), 'freq': freq})

    return result

def query_pattern_from_side(pattern, which_side, corpus, comment_type=None, regex_enable=False, breakpoint_1=0.3, breakpoint_2=0.7):
    
    # n_gram_freq_dist_of_utt_containg_keyword = FreqDist()
    # n_gram_freq_dist_of_the_other_utt = FreqDist()

    author_counter = Counter()

    re_pattern = re.compile(pattern)
    
    result = {
        "statistics": {
            "total": 0,
            "author_type": 0,
            "author_diversity": 0
        },
        "data": []
    }

    key = {
        "first": "comment",
        "second": "recomment",
        "both": "both"
    }

    list_of_turn_position_of_word = list()
    list_of_utterance_position_of_word = list()


    # 選任意一邊出現的
    if which_side == 'any':

        for pair in corpus:

            match_first_turn = re_pattern.search(pair['comment_content'])
            match_second_turn = re_pattern.search(pair['recomment_content'])

            if match_first_turn or match_second_turn:



                for matched_pattern in re_pattern.finditer(pair['comment_content']):

                    if 'comment_content_turn_position' not in pair:
                        pair['comment_content_turn_position'] = list()

                    if 'comment_content_turn_position' not in pair:
                        pair['comment_content_utterance_position'] = list()

                    pos = get_pattern_position_in_a_string(pair['comment_content'], matched_pattern.start(), matched_pattern.end())
                    list_of_turn_position_of_word.append(pos) 
                    pair['comment_content_turn_position'].append(pos)

                    pos = get_pattern_position_in_an_utterance(pair['comment_content'], matched_pattern.start(), matched_pattern.end())
                    list_of_utterance_position_of_word.append(pos)
                    pair['comment_content_utterance_position'].append(pos)


                for matched_pattern in re_pattern.finditer(pair['recomment_content']):

                    if 'recomment_content_turn_position' not in pair:
                        pair['recomment_content_turn_position'] = list()

                    if 'recomment_content_utterance_position' not in pair:
                        pair['recomment_content_utterance_position'] = list()
                    
                    pos = get_pattern_position_in_a_string(pair['recomment_content'], matched_pattern.start(), matched_pattern.end())
                    list_of_turn_position_of_word.append(pos) 
                    pair['recomment_content_turn_position'].append(pos)

                    pos = get_pattern_position_in_an_utterance(pair['recomment_content'], matched_pattern.start(), matched_pattern.end())
                    list_of_utterance_position_of_word.append(pos)
                    pair['recomment_content_utterance_position'].append(pos)


    
                result['data'].append(pair)
                

    # 選兩邊都出現的
    elif which_side == 'both':
        
        for pair in corpus:

            match_first_turn = re_pattern.search(pair['comment_content'])
            match_second_turn = re_pattern.search(pair['recomment_content'])

            if match_first_turn and match_second_turn:

                for matched_pattern in re_pattern.finditer(pair['comment_content']):
                    pos = get_pattern_position_in_a_string(pair['comment_content'], matched_pattern.start(), matched_pattern.end())
                    list_of_turn_position_of_word.append(pos) 
                    pair['comment_content_turn_position'] = pos

                    pos = get_pattern_position_in_an_utterance(pair['comment_content'], matched_pattern.start(), matched_pattern.end())
                    list_of_utterance_position_of_word.append(pos)
                    pair['comment_content_utterance_position'] = pos

                for matched_pattern in re_pattern.finditer(pair['recomment_content']):
                    pos = get_pattern_position_in_a_string(pair['recomment_content'], matched_pattern.start(), matched_pattern.end())
                    list_of_turn_position_of_word.append(pos) 
                    pair['recomment_content_turn_position'] = pos

                    pos = get_pattern_position_in_an_utterance(pair['recomment_content'], matched_pattern.start(), matched_pattern.end())
                    list_of_utterance_position_of_word.append(pos)
                    pair['recomment_content_utterance_position'] = pos

                result['data'].append(pair)


    # 選回文 or 回回文的
    else:
        
        for pair in corpus:

            utterance = pair[key[which_side] + '_content']
            other_side_utterance =  pair['recomment_content'] if key[which_side] == 'comment' else pair['comment_content']

            match_turn = re_pattern.search(utterance)

            if match_turn:

                for matched_pattern in re_pattern.finditer(utterance):

                    pos = get_pattern_position_in_a_string(utterance, matched_pattern.start(), matched_pattern.end())
                    list_of_turn_position_of_word.append(pos) 
                    pair[key[which_side] + '_content_turn_position'] = pos

                    pos = get_pattern_position_in_an_utterance(utterance, matched_pattern.start(), matched_pattern.end())
                    list_of_utterance_position_of_word.append(pos)
                    pair[key[which_side] + '_content_utterance_position'] = pos


                result['data'].append(pair)
                author_counter[pair[key[which_side] + '_user']] += 1

                # 計算 n-gram
                # n_gram_freq_dist_of_utt_containg_keyword = generate_n_gram_freq_dist(utterance, n_gram_freq_dist_of_utt_containg_keyword, 2)
                # n_gram_freq_dist_of_the_other_utt = generate_n_gram_freq_dist(other_side_utterance, n_gram_freq_dist_of_the_other_utt, 2)

        # result['statistics']['word_position'] = round(sum(list_of_turn_position_of_word) / len(list_of_turn_position_of_word), 2)
        
        # result['statistics']['n_gram_freq_dist_of_utt_containg_keyword'] = change_tuple_dict_key_to_str_dict_key(n_gram_freq_dist_of_utt_containg_keyword.most_common(30))
        # result['statistics']['n_gram_freq_dist_of_the_other_utt'] = change_tuple_dict_key_to_str_dict_key(n_gram_freq_dist_of_the_other_utt.most_common(30))


    # result['statistics']['total'] = sum(author_counter.values())
    # result['statistics']['author_type'] = len(author_counter.keys())
    result['statistics']['turn_position_distribution'] = calculate_word_position_distribution(list_of_turn_position_of_word, breakpoint_1, breakpoint_2)
    result['statistics']['utterance_position_distribution'] = calculate_word_position_distribution(list_of_utterance_position_of_word, breakpoint_1, breakpoint_2)

    if result['statistics']['total'] == 0:
        result['statistics']['author_diversity'] = 0
    else:
        result['statistics']['author_diversity'] = round(result['statistics']['author_type'] / result['statistics']['total'], 2)
    
    return jsonify(result)
