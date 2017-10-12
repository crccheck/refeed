import json
import os
from xml.etree import ElementTree as ET

from aiohttp import web
from lxml.html import document_fromstring
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
    """
    Build the context needed to replace item fields
    """
    data = {
        'description': '',
    }

    jsonld_elem = tree.find('./head/script[@type="application/ld+json"]')
    if jsonld_elem is not None:
        jsonld = json.loads(jsonld_elem.text)
        data['description'] = """
            <img src="{thumbnailUrl}" width="300" style="float: left; margin-right: 5px; max-width: 100%;" />
            <p>{description}</p>
        """.format(**jsonld)

    return data


async def refeed(request):
    try:
        feed_url = request.GET['feed']
    except KeyError:
        return web.Response(status=400, text='Must supply a ?feed=<rss url>')

    pass_thru_headers = {}
    async with aiohttp.ClientSession() as session:  # TODO headers=
        try:
            resp = await session.get(feed_url)
        except ValueError as e:
            return web.Response(status=400, text=str(e))
        pass_thru_headers['Content-Type'] = resp.headers['Content-Type']
        # assert pass_thru_headers['Content-Type'] == application/rss+xml
        tree = ET.fromstring(await resp.text())
        for item in tree.findall('.//item')[:1]:  # DEBUG enable for all items after Redis
            item_details = get_item_details(item)
            resp = await session.get(item_details['link'])
            # XML can take a file-like object but aiohttp's read() isn't file-like
            article_tree = document_fromstring(await resp.read())
            data = build_item(article_tree)
            for k, v in data.items():
                node = item.find('./' + k)
                node.text = data[k]
    return web.Response(text=ET.tostring(tree).decode('utf-8'), headers=pass_thru_headers)


app = web.Application()
app.router.add_get('/refeed/', refeed)

if not os.getenv('CI'):
    port = os.getenv('PORT', 8080)
    web.run_app(app, port=port)
