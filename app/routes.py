'''API v1 routes'''

import requests
from bs4 import BeautifulSoup, NavigableString
import flask
from . import app

@app.route('/v1/article', methods=['GET'])
def get_article():
    '''Scrape, transform, and return specified article as array of letters'''
    article_url = flask.request.args.get('url')
    if article_url is None:
        return {'message': 'No url specified'}, 400

    article_res = requests.get(article_url, timeout=5)
    body = BeautifulSoup(article_res.text, 'html.parser')
    article = body.find('div', id='mw-content-text')

    response = {}

    # get image from infobox
    info_box = body.find('table', class_='infobox')
    if info_box is not None:
        primary_img = info_box.find('img')
        primary_img_src = primary_img.attrs['src'].replace('//', '')
        response['primaryImgSrc'] = primary_img_src

    # get all image sources and their captions
    images = []
    for figure in article.find_all('figure'):
        img = figure.find('img')
        if img is None:
            continue
        src = img.attrs['src'].replace('//', '')    # srcs are prefixed with '//'
        caption = figure.find('figcaption').get_text()
        images.append({'src': src, 'caption': caption})
    response['images'] = images

    # get text passage from article
    clean_article(article)
    passage = recursive_append_text(article)
    response['passage'] = passage

    return response


def clean_article(article):
    '''Remove references, h2, figures, notes, .infobox, .shortdescription, .mw-editsection'''
    decompose_all(article.find_all(class_='reference'))
    decompose_all(article.find_all('h2'))
    decompose_all(article.find_all('figure'))
    decompose_all(article.find_all(attrs={'role': 'note'}))
    decompose_all(article.find_all(class_='infobox'))
    decompose_all(article.find_all(class_='shortdescription'))
    decompose_all(article.find_all(class_='mw-editsection'))

def decompose_all(elements):
    '''Call bs tag.decompose on all elements in iterable'''
    for elem in elements:
        elem.decompose()


def recursive_append_text(element, text=''):
    '''Get text and annotation ranges'''
    if isinstance(element, NavigableString) or len(element.contents) == 0:
        return element.get_text().replace('\n', '')

    inner_text = ''
    for child in element.contents:
        inner_text += recursive_append_text(child, text)
    if element.name == 'p' and len(element.contents) > 0:
        # inner_text += '\nabcdefghijklmnop\n'
        inner_text += '\n'
    return inner_text
