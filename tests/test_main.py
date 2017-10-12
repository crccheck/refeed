import os
from xml.etree import ElementTree as ET

import pytest
from lxml.html import parse as html5_parse

from ..main import (
    build_item,
    get_feed_details,
    get_item_details,
)


@pytest.fixture
def tree():
    path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'fixtures', 'ad-rss.xml')
    return ET.parse(path).getroot()


@pytest.fixture
def html_tree():
    path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'fixtures', 'article.html')
    return html5_parse(path)


def test_get_feed_details(tree):
    details = get_feed_details(tree)
    assert details['link'] == 'https://www.architecturaldigest.com'


def test_get_item_details(tree):
    item = tree.find('.//item')
    details = get_item_details(item)
    assert details['link'] == 'https://www.architecturaldigest.com/story/why-high-gloss-paint-should-be-on-your-radar'
    assert details['guid'] == '59df9cf1f7610e67d7f16a0b'


def test_build_item(html_tree):
    item = build_item(html_tree)
    assert item['title'] == 'Why High-Gloss Paint Should Be on Your Radar'
    assert 'https://media.architecturaldigest.com/photos/59dfb79cc9ed4c222543c068/master/pass/high-gloss-paint-1.jpg' in item['description']
    assert 'Plus tons of ideas for using it around the house' in item['description']
