import os
from xml.etree import ElementTree as ET

import pytest

from ..main import get_feed_details, get_item_details


@pytest.fixture
def tree():
    path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'fixtures', 'ad-rss.xml')
    return ET.parse(path).getroot()


def test_get_feed_details(tree):
    details = get_feed_details(tree)
    assert details['link'] == 'https://www.architecturaldigest.com'


def test_get_item_details(tree):
    item = tree.find('.//item')
    details = get_item_details(item)
    assert details['link'] == 'https://www.architecturaldigest.com/story/why-high-gloss-paint-should-be-on-your-radar'
    assert details['guid'] == '59df9cf1f7610e67d7f16a0b'
