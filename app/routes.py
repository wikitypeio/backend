import requests
from bs4 import BeautifulSoup, NavigableString
import flask
import json
from . import app

@app.route("/v1/article", methods=['GET'])
def get_article():
    '''Scrape, transform, and return specified article as array of letters'''
    article_url = flask.request.args.get('url')
    if article_url is None:
        return {"message": "No url specified"}, 400

    try:
        res = requests.get(article_url, timeout=5)
        if res.status_code != 200:
            raise ConnectionError("Error fetching article")
    except requests.exceptions.ConnectTimeout as e:
        print("TIMED OUT")
        return {"message": f"{e}"}, 500
    except ConnectionError as e:
        return {"message": f"{e}"}, 500



    return {"message": "Hello world! Success!", "data": res.json()}
