from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
from flask import session
import torch
import numpy as np
import dill as pickle
import model
from segmentation import Segmentation
import re

app = Flask(__name__)
app.config['SECRET_KEY'] = 'the quick brown fox jumps over the lazy dog'
app.config['CORS_HEADERS'] = 'Content-Type'
cors = CORS(app)
session = []

TEXT = pickle.load(open(f'TEXT.pkl', 'rb'))
model = model.LSTM(2764, 300, 128, 1,
                   2, True, 0.5, TEXT.vocab.stoi[TEXT.pad_token])
TOKENIZER = lambda x: x.split()
model.load_state_dict(torch.load('lstm.pt',map_location=lambda storage, location: 'cpu'))

@app.route('/', methods=['GET'])
def index():
    return jsonify('API Service Base')

@app.route('/api/prediction', methods=['GET'])
def get_prediction():
    result = []
    try:
        model_result = session[0]
        result.append({
            'text': model_result['text'],
            'label': model_result['label']
        })
    except:
        result.append({
            'text': 'Text Input',
            'label': 'Sentiment Polarity'
        })
    session.clear()
    return jsonify(result)

@app.route('/api/prediction', methods=['POST'])
def make_prediction():
    txt = request.get_json()['text']
    model.eval()
    # Clean the data from the raw input
    sentence = clean_data(np.array([txt]))
    # Segment and tokenize the clean data
    tokenized = [TOKENIZER(t) for t in Segmentation(sentence).runSegmentation()]
    indexed = [TEXT.vocab.stoi[t] for t in tokenized[0]]
    length = [len(indexed)]

    tensor = torch.LongTensor(indexed).unsqueeze(1)
    length_tensor = torch.LongTensor(length)
    prediction = torch.sigmoid(model(tensor, length_tensor))

    result = {
        'text': txt,
        'label': prediction.item()
    }
    session.append(result)
    return jsonify({'result':result})

def clean_data(texts):
    """
    Function to clean data, strip off the noises.
    """
    for i, t in enumerate(texts):
        RE_EMOJI = re.compile('[\U00010000-\U0010ffff]', flags=re.UNICODE) # Adapted from https://www.reddit.com/r/learnpython/comments/8br5sz/removing_emojis_from_words_python3/
        t = RE_EMOJI.sub(r'', t)
        t = re.sub(r' ‌', '',t)
        t = re.sub(r'[A-Za-z.0-9၀၁၂၃၄၅၆၇၈၉?!@#$%^&*(),:;၊။/-=_~]', '', t)
        t = re.sub(u'\u200b', '', t)
        t = re.sub(u'\u200c', '', t)
        t = re.sub(u'\u200d', '', t)
        t = re.sub(u'\ufeff', '', t)
        t = re.sub(u'\u0027', '', t)
        t = re.sub(r'"','',t)
        texts[i] = t

    return texts

if __name__ == '__main__':
    app.run(debug=True)
