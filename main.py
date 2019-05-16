import json
import logging
import os
from functools import lru_cache
from xml.etree import ElementTree as ET
from typing import Dict

from aiohttp import web
from lxml.html import document_fromstring
import aiohttp

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


DESCRIPTION_FMT = """
<img src="{thumbnailUrl}" width="300" style="float: left; margin-right: 5px; max-width: 100%;" />
<p>{description}</p>
""".format


def get_item_details(item: ET.Element) -> Dict:
    # Should I return a namedtuple?
    return {
        'link': item.find('./link').text,
        'guid': item.find('./guid').text,
    }


def build_item_context(tree) -> Dict:
    """
    Build the context needed to replace item fields
    """
    data = {
        'description': '',
    }

    jsonld_elem = tree.find('./head/script[@type="application/ld+json"]')
    if jsonld_elem is not None:
        jsonld = json.loads(jsonld_elem.text)
        data['description'] = DESCRIPTION_FMT(**jsonld)

    return data


async def refeed(request):
    try:
        feed_url = request.query['feed']
    except KeyError:
        return web.Response(status=400, text='Must supply a ?feed=<rss url>')

    logger.info('Processing feed: %s', feed_url)

    async with aiohttp.ClientSession() as session:  # TODO headers=
        @lru_cache(maxsize=120)
        async def fetch_seo_context(url: str):
            logger.info('Fetching: %s', url)
            resp = await session.get(url)
            # XML can take a file-like object but aiohttp's read() isn't file-like
            article_tree = document_fromstring(await resp.read())
            print('uncached!', url)
            return build_item_context(article_tree)

        try:
            resp = await session.get(feed_url)
        except ValueError as e:
            return web.Response(status=400, text=str(e))

        tree = ET.fromstring(await resp.text())
        items = tree.findall('.//item')
        if not items:
            return web.Response(status=400, text='No items found')

        for item in items:
            details = get_item_details(item)
            context = await fetch_seo_context(details['link'])

            # Re-write XML
            for k, v in context.items():
                node = item.find('./' + k)
                node.text = context[k]

    return web.Response(
        text=ET.tostring(tree).decode('utf-8'),
        content_type='application/rss+xml')


app = web.Application()
app.router.add_get('/refeed/', refeed)

if not os.getenv('CI'):
    port = int(os.getenv('PORT', 8080))
    web.run_app(app, port=port)
