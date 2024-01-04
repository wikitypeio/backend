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
    for reference_elem in article.find_all(class_='reference'):
        reference_elem.decompose()
    for heading in article.find_all('h2'):
        heading.decompose()
    for fig in article.find_all('figure'):
        fig.decompose()
    for note in article.find_all(attrs={'role': 'note'}):
        note.decompose()
    article.find(class_='infobox').decompose()
    article.find(class_='shortdescription').decompose()
    for edit in article.find_all(class_='mw-editsection'):
        edit.decompose()


def recursive_append_text(element, text=''):
    '''Get text and annotation ranges'''
    if isinstance(element, NavigableString) or len(element.contents) == 0:
        return element.get_text().replace('\n', '')

    inner_text = ''
    for child in element.contents:
        inner_text += recursive_append_text(child, text)
    # if element.name == 'p':
        # inner_text += '\nabcdefghijklmnop\n'
    return inner_text
