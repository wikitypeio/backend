'''API v1 routes'''

import time
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
        caption = figure.find('canvas')
        caption_text = None
        if caption is not None:
            caption_text = caption.get_text()
        images.append({'src': src, 'caption': caption_text})
    response['images'] = images

    # get text passage from article
    # all cleaning of article div contents must happen prior to extracting
    #   contents data because link and decoration ranges depend on indices
    #   within the plaintext string
    clean_article(article)
    tracked_elements = []
    plain_text = recursive_append_text(article, tracked_elements)
    response['passage'] = {'plaintext': plain_text, 'elementRanges': tracked_elements}

    return response


def clean_article(article):
    '''Remove:
        references, h2, tables, figures, notes, thumbs, .infobox,
        .shortdescription, .mw-editsection, .reflist'''
    decompose_all(article.find_all(class_='reference'))
    decompose_all(article.find_all('h2'))
    decompose_all(article.find_all('table'))
    decompose_all(article.find_all('figure'))
    decompose_all(article.find_all(attrs={'role': 'note'}))
    decompose_all(article.find_all(class_='thumb'))
    decompose_all(article.find_all(class_='infobox'))
    decompose_all(article.find_all(class_='shortdescription'))
    decompose_all(article.find_all(class_='mw-editsection'))
    decompose_all(article.find_all(class_='reflist'))

def decompose_all(elements):
    '''Call bs tag.decompose on all elements in iterable'''
    for elem in elements:
        elem.decompose()


# Using dictionary for total_text so all references point to same object
def recursive_append_text(element, tracked_elements,
                          total_text_dict={'total_text': ''}):
    '''Get text and annotation ranges'''
    if isinstance(element, NavigableString) or len(element.contents) == 0:
        return element.get_text().replace('\n', '')

    inner_text = ''
    for child in element.contents:
        inner_text += recursive_append_text(child, tracked_elements,
                                            total_text_dict=total_text_dict)
    total_text_dict['total_text'] += inner_text

    track_range(element, is_link_to_article, link_transform, tracked_elements,
                len(total_text_dict['total_text']), len(inner_text))
    return inner_text

def track_range(el, el_predicate, el_transform, tracking_list, start, length):
    '''If element passes el_predicate, add el_transform(el) to list'''
    if el_predicate(el):
        base_obj = el_transform(el)
        tracked_obj = {**base_obj, 'start': start, 'end': start + length + 1}
        tracking_list.append(tracked_obj)

def is_link_to_article(element):
    '''Determine if link is to another article on wikipedia and should be added
        to list of link ranges'''
    return element.name == 'a' and element.attrs['href'][0] == '/'

def link_transform(element):
    '''Transform link elements'''
    return {'type': 'link', 'href': element.attrs['href']}
