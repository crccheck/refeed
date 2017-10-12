import json
import os
from xml.etree import ElementTree as ET

from aiohttp import web
from lxml.html import parse as html5_parse
import aiohttp


def get_feed_details(tree):
    """
    Get the details about the feed

    WIP not sure what to do with this information yet
    """
    elems = tree.find('./channel').getchildren()
    children = [x for x in elems if x.tag != 'item']
    details = {x.tag: x.text for x in children}
    return details


def get_item_details(item):
    return {
        'link': item.find('./link').text,
        'guid': item.find('./guid').text,
    }


def build_item(tree):
    data = {
        'title': '',
        # 'link' This will come from the original RSS item
        'description': '',
        # 'guid' This will come from the original RSS item
    }

    jsonld_elem = tree.find('./head/script[@type="application/ld+json"]')
    if jsonld_elem is not None:
        jsonld = json.loads(jsonld_elem.text)
        data['title'] = jsonld['headline']
        data['description'] = """
            <img src="{thumbnailUrl}" style="float: left; margin-right: 5px;" />
            <p>{description}</p>
        """.format(**jsonld)

    return data


async def refeed(request):
    try:
        feed_url = request.GET['feed']
    except KeyError:
        return web.Response(status=400, text='Must supply a ?feed=<rss url>')

    try:
        pass_thru_headers = {}
        async with aiohttp.ClientSession() as session:  # TODO headers=
            resp = await session.get(feed_url)
            # Should be: application/rss+xml
            pass_thru_headers['Content-Type'] = resp.headers['Content-Type']
            text = await resp.text()
            tree = ET.fromstring(text)
            for item in tree.findall('.//item'):
                item_details = get_item_details(item)
                # resp = await session.get(item_details['link'))
                # article_tree = html5_parse(resp)
        return web.Response(text=text, headers=pass_thru_headers)
    except ValueError as e:
        return web.Response(status=400, text=str(e))


app = web.Application()
app.router.add_get('/refeed/', refeed)

if not os.getenv('CI'):
    port = os.getenv('PORT', 8080)
    web.run_app(app, port=port)
