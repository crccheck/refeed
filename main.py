import os
from xml.etree import ElementTree as ET

from aiohttp import web
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


async def refeed(request):
    try:
        feed_url = request.GET['feed']
    except KeyError:
        return web.Response(status=400, text='Must supply a ?feed=<rss url>')

    try:
        async with aiohttp.ClientSession() as session:  # headers=
            resp = await session.get(feed_url)
            text = await resp.text()
        tree = ET.fromstring(text)
        for item in tree.findall('.//item'):
            item_details = get_item_details(item)
        return web.Response(text=text)
    except ValueError as e:
        return web.Response(status=400, text=str(e))


app = web.Application()
app.router.add_get('/refeed/', refeed)

if not os.getenv('CI'):
    port = os.getenv('PORT', 8080)
    web.run_app(app, port=port)
