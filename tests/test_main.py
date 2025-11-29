import os
from xml.etree import ElementTree as ET

import pytest
from lxml.html import parse as html_parse

from ..main import build_item_context


@pytest.fixture
def tree():
    path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "fixtures", "ad-rss.xml")
    return ET.parse(path).getroot()


@pytest.fixture
def html_article_tree():
    path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "fixtures", "article.html")
    return html_parse(path)


@pytest.fixture
def html_gallery_tree():
    path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "fixtures", "gallery.html")
    return html_parse(path)


@pytest.fixture
def html_gizmodo_tree():
    path = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "fixtures", "gizmodo-article.html"
    )
    return html_parse(path)


def test_build_article(html_article_tree):
    item = build_item_context(html_article_tree)
    assert (
        "https://media.architecturaldigest.com/photos/59dfb79cc9ed4c222543c068"
        in item["description"]
    )
    assert "" in item["description"]


def test_build_gallery(html_gallery_tree):
    item = build_item_context(html_gallery_tree)
    assert (
        "https://media.architecturaldigest.com/photos/5d8a61eae019b900089bc319"
        in item["description"]
    )
    assert "" in item["description"]


def test_build_gizmodo_graph(html_gizmodo_tree):
    """Test handling of JSON-LD @graph structure with WebPage type"""
    item = build_item_context(html_gizmodo_tree)
    # Should extract description from WebPage in @graph
    assert "Mamoru Oshii's cult classic" in item["description"]
    # Should extract thumbnailUrl from WebPage
    assert (
        "https://gizmodo.com/app/uploads/2025/11/Angels-Egg-io9-2025-retro-review.jpg"
        in item["description"]
    )
    # Should contain img tag
    assert "<img" in item["description"]
