import argparse
import functools
import os
import sys
import time
from datetime import datetime

from flask import request, Flask, render_template
from flask_cors import CORS

from masr import SUPPORT_MODEL
from masr.predict import Predictor
from masr.utils.audio_vad import crop_audio_vad
from masr.utils.utils import add_arguments, print_arguments

parser = argparse.ArgumentParser(description=__doc__)
add_arg = functools.partial(add_arguments, argparser=parser)
add_arg('use_model',        str,    'deepspeech2',        "所使用的模型", choices=SUPPORT_MODEL)
add_arg("host",             str,    "127.0.0.1",            "监听主机的IP地址")
add_arg("port",             int,    5028,                 "服务所使用的端口号")
add_arg("base_path",        str,    "../reread-server/storage/app/rs/",    "待识别文件所在目录")
add_arg('use_gpu',          bool,   True,   "是否使用GPU预测")
add_arg('to_an',            bool,   False,  "是否转为阿拉伯数字")
add_arg('use_pun',          bool,   False,  "是否给识别结果加标点符号")
add_arg('beam_size',        int,    300,    "集束搜索解码相关参数，搜索大小，范围:[5, 500]")
add_arg('alpha',            float,  2.2,    "集束搜索解码相关参数，LM系数")
add_arg('beta',             float,  4.3,    "集束搜索解码相关参数，WC系数")
add_arg('cutoff_prob',      float,  0.99,   "集束搜索解码相关参数，剪枝的概率")
add_arg('cutoff_top_n',     int,    40,     "集束搜索解码相关参数，剪枝的最大值")
add_arg('vocab_path',       str,    'dataset/vocabulary.txt',    "数据集的词汇表文件路径")
add_arg('model_path',       str,    'models/{}_{}/inference.pt', "导出的预测模型文件路径")
add_arg('pun_model_dir',    str,    'models/pun_models/',        "加标点符号的模型文件夹路径")
add_arg('lang_model_path',  str,    'lm/zh_giga.no_cna_cmn.prune01244.klm',    "集束搜索解码相关参数，语言模型文件路径")
add_arg('feature_method',   str,    'linear',             "音频预处理方法", choices=['linear', 'mfcc', 'fbank'])
add_arg('decoder',          str,    'ctc_beam_search',    "结果解码方法",   choices=['ctc_beam_search', 'ctc_greedy'])
add_arg('pinyin_mode',      bool,   False,                 '使用拼音识别模式')
args = parser.parse_args()

app = Flask(__name__, template_folder="templates", static_folder="static", static_url_path="/")
# 允许跨越访问
CORS(app)

predictor = Predictor(model_path=args.model_path.format(args.use_model, args.feature_method), vocab_path=args.vocab_path, use_model=args.use_model,
                      decoder=args.decoder, alpha=args.alpha, beta=args.beta, lang_model_path=args.lang_model_path,
                      beam_size=args.beam_size, cutoff_prob=args.cutoff_prob, cutoff_top_n=args.cutoff_top_n,
                      use_gpu=args.use_gpu, use_pun_model=args.use_pun, pun_model_dir=args.pun_model_dir,
                      pinyin_mode=args.pinyin_mode,
                      feature_method=args.feature_method)


# 语音识别接口
@app.route("/recognition", methods=['GET'])
def recognition():
    fname = request.args.get('fname','')
    if fname!='':
        if fname.startswith('/'):
            file_path = fname
        else:
            file_path = os.path.join(args.base_path, fname)
        try:
            start = time.time()
            # 执行识别
            score, text = predictor.predict(audio_path=file_path, to_an=args.to_an)
            end = time.time()
            print("识别时间：%dms，识别结果：%s， 得分: %f" % (round((end - start) * 1000), text, score))
            result = str({"code": 0, "msg": "success", "result": text, "score": round(score, 3)}).replace("'", '"')
            return result
        except Exception as e:
            print(f'[{datetime.now()}] 短语音识别失败，错误信息：{e}', file=sys.stderr)
            return str({"error": 1, "msg": "audio read fail!"})
    return str({"error": 3, "msg": "audio is None!"})

@app.route('/')
def home():
    return ("Internal use only")


if __name__ == '__main__':
    print_arguments(args)
    app.run(host=args.host, port=args.port)
