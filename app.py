import os
import sys
from collections import Counter
import pickle
import re
from itertools import repeat, chain

from flask import Flask, jsonify, request
from flask_cors import CORS
# from gensim.models.wrappers import FastText
# from sklearn.metrics.pairwise import cosine_similarity
from gensim.models.fasttext import load_facebook_model
from nltk import FreqDist
from nltk.util import ngrams

sys.path.insert(0, '/usr/src')
from app.helper import *

print(sys.path)


app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
CORS(app)

# 載入模型 (大約要 1 分鐘)
model = load_facebook_model('fasttext-cc.zh.300.bin')
# model = None

with open("womentalk_2019_pair.pickle", "rb") as f:
    corpus = pickle.load(f)

def _similarity(content):
    print('content')
    print(content)
    slot_number = len(content['target'])
    score_list = []

    for candidate in content['candidates']:
        sim = 0
        for i, w in enumerate(candidate):
    #         print(i)
    #         print(w)
            # sim += similarity(a['target'][i], w)
            sim += model.wv.similarity(content['target'][i], w)
        sim = sim / slot_number
        # print(sim)
        score_list.append(sim)
    
    result = [{'score': round(_, 2), 'candidate': x} for _, x in sorted(zip(score_list, content['candidates']), reverse=True) if _ > 0] 

    return jsonify({'status': 'success', 'sorted_candidates': result})


@app.route('/similarity')
def similarity():
    content = request.json
    # 傳來的 json 格式如下:
    # 整個 [無聊] 到 [不行]
    # {target: [無聊, 不行], candidates: [[嗨, 不行], [傻眼, 想死], ...]}

    return _similarity(content)

@app.route('/query')
def query():
    query_pattern = request.args.get("pattern")
    comment_type = request.args.get("comment_type", None)
    which_side = request.args.get("which_side")
    regex_enable = True if request.args.get("regex_enable") == 'true' else False

    return query_pattern_from_side(query_pattern, which_side, corpus, comment_type, regex_enable)


@app.route('/construction_extractor')
def construction_extractor():
    query_pattern = request.args.get("pattern")
    parsed_query = parse_query(query_pattern)

    print(parsed_query)

    target = []
    candidates = set()

    for e in parsed_query:
        if e['type'] == 'slot':
            target.append(e['word'])

    print(target)

    ptn = convert_to_regex(parsed_query)
    ptn = re.compile(ptn)

    for pair in corpus:
        # comment_findall = re.findall(ptn, pair['comment_content'])
        # recomment_findall = re.findall(ptn, pair['recomment_content'])
        finditer = re.finditer(ptn, pair['comment_content'] + pair['recomment_content'])

        for found in finditer:
            candidates.add(found.groups())

        # if len(comment_findall) > 0:
        #     for found_pair in comment_findall:
        #         candidates.add(found_pair)

        # if len(comment_findall) > 0:
        #     for found_pair in recomment_findall:
        #         candidates.add(found_pair)


    return _similarity({'target': target, 'candidates': list(candidates)})

@app.route('/get_sentence')
def get_sentence():
    query_pattern = request.args.get("pattern")
    window_size = request.args.get("window_size", 10, type=int)

    results = []

    for pair in corpus:

        for m in re.finditer(query_pattern, pair['comment_content']):
            left = max(0, m.start() - window_size)
            right = min(len(pair['comment_content']), m.end() + window_size)
            results.append(pair['comment_content'][left:right])

        for m in re.finditer(query_pattern, pair['recomment_content']):
            left = max(0, m.start() - window_size)
            right = min(len(pair['recomment_content']), m.end() + window_size)
            results.append(pair['recomment_content'][left:right])

    return jsonify(results)

#we define the route /
@app.route('/')
def welcome():
    # return a json
    return jsonify({'status': 'api working'})



if __name__ == '__main__':
    #define the localhost ip and the port that is going to be used
    # in some future article, we are going to use an env variable instead a hardcoded port 
    app.run(host='0.0.0.0', port=os.getenv('PORT'))
