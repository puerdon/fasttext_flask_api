import os
from flask import Flask, jsonify
from gensim.models.wrappers import FastText

app = Flask(__name__)

# 載入模型 (大約要 1 分鐘)
model = FastText.load_fasttext_format('/home/yongfu/fasttext-cc.zh.300.bin')



#we define the route /
@app.route('/')
def welcome():
    # return a json
    return jsonify({'status': 'api working'})

if __name__ == '__main__':
    #define the localhost ip and the port that is going to be used
    # in some future article, we are going to use an env variable instead a hardcoded port 
    app.run(host='0.0.0.0', port=os.getenv('PORT'))