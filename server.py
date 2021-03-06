from flask import Flask, request
from flask_cors import CORS, cross_origin

from modules import KerasContext, KerasBatchedInferenceProvider
from modules import ONNXContext, ONNXBatchedInferenceProvider

import os, sys 

ONNX_MODEL_PATH = './model/pnuemonia.onnx'
HD5_MODEL_PATH = './model/pnuemonia.h5'

if not os.path.exists(ONNX_MODEL_PATH):
    print('ONNX Model not found.run onnx.py')

runtime_provider_fn = None
runtime = "onnx"

try:
    context = ONNXContext(ONNX_MODEL_PATH)
    batched_provider = ONNXBatchedInferenceProvider(context, wait = False)
    runtime_provider_fn = batched_provider.add_to_batch
    print('Running with ONNX Runtime')

except :
    context = KerasContext(HD5_MODEL_PATH)
    batched_provider = KerasBatchedInferenceProvider(context, wait = False)
    runtime_provider_fn = batched_provider.add_to_batch
    print('Running with Keras runtime, fallback to normal execution provider.')
    runtime = "keras-tensorflow"


app = Flask(__name__)
CORS(app, support_credentials=True)

@app.route("/api/status")
@cross_origin(supports_credentials=True)
def status():

    return {
        "status" : "active",
        "runtime" : runtime,
        "success" : True
    }

@app.route("/api/infer", methods = ['POST'])
def infer():

    image = request.files['image']
    image = image.stream.read()

    isinfer, result = runtime_provider_fn(image)
       #onnx run time execution
    if isinfer :
        return {
            "success" : True,
            "isinfer" : True,
            "result" : result,
            "remaining" : 0,
            "runtime" : runtime
        }
    
    else :
        #keras runtime execution
        return {
            "success" : True,
            "isinfer" : False,
            "result" : "Model has wait enabled in batch model",
            "remaining" : result,
            "runtme" : runtime
        }

#standard port number
app.run('0.0.0.0', port = 5000)
