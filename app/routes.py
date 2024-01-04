'''API v1 routes'''

import requests
from bs4 import BeautifulSoup, NavigableString
import flask
from . import app

@app.route("/v1/article", methods=['GET'])
def get_article():
    '''Scrape, transform, and return specified article as array of letters'''
    article_url = flask.request.args.get('url')
    if article_url is None:
        return {"message": "No url specified"}, 400

    res = requests.get(article_url, timeout=5)
    soup = BeautifulSoup(res.text, 'html.parser')
    article = soup.find('div', class_='mw-parser-output')

    clean_article(article)

    # get image from infobox
    info_box = article.find('table', class_="infobox")
    primary_img = info_box.find('img')
    primary_img_src = primary_img.attrs['src'].replace('//', '')

    # get all image sources and their captions
    images = []
    for figure in article.find_all('figure'):
        img = figure.find('img')
        if img is None:
            continue
        src = img.attrs['src'].replace('//', '')    # srcs are prefixed with '//'
        caption = figure.find("figcaption").get_text()
        images.append({"src": src, "caption": caption})

    passage = recursive_append_text(article)

    return {"images": images, "primaryImgSrc": primary_img_src, "passage": passage}


def clean_article(article):
    '''Remove references'''
    for reference_elem in article.find_all(class_='reference'):
        reference_elem.decompose()


def recursive_append_text(element, text=''):
    '''Get text and annotation ranges'''
    if isinstance(element, NavigableString) or len(element.contents) == 0:
        return element.get_text()

    inner_text = ''
    for child in element.contents:
        inner_text += recursive_append_text(child, text)
    return inner_text
