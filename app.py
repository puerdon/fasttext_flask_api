import os
from flask import Flask, jsonify, request
# from gensim.models.wrappers import FastText
# from sklearn.metrics.pairwise import cosine_similarity
from gensim.models.fasttext import load_facebook_model

app = Flask(__name__)

# 載入模型 (大約要 1 分鐘)
model = load_facebook_model('fasttext-cc.zh.300.bin')



#we define the route /
@app.route('/')
def welcome():
    content = request.json
    # 傳來的 json 格式如下:
    # 整個 [無聊] 到 [不行]
    # {target: [無聊, 不行], candidates: [[嗨, 不行], [傻眼, 想死], ...]}

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
    
    result = [{'score': _, 'candidate': x} for _, x in sorted(zip(score_list, content['candidates']), reverse=True)] 

    return jsonify({'status': 'api working', 'sorted_candidates': result})

if __name__ == '__main__':
    #define the localhost ip and the port that is going to be used
    # in some future article, we are going to use an env variable instead a hardcoded port 
    app.run(host='0.0.0.0', port=os.getenv('PORT'))
