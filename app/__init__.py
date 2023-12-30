from flask import Flask
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route("/")
def hello_world():
    '''Testing'''
    return {"message": "Hello world! Success!"}
