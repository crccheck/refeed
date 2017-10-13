import json
import os
from xml.etree import ElementTree as ET

from aiohttp import web
from lxml.html import document_fromstring
import aiohttp
import redis

cache = None


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


def build_item_context(tree):
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

    all_details = []
    raw_context_to_save = {}

    async with aiohttp.ClientSession() as session:  # TODO headers=
        try:
            resp = await session.get(feed_url)
        except ValueError as e:
            return web.Response(status=400, text=str(e))

        pass_thru_headers = {
            'Content-Type': resp.headers['Content-Type'],
        }
        # assert pass_thru_headers['Content-Type'] == application/rss+xml
        tree = ET.fromstring(await resp.text())
        items = tree.findall('.//item')

        # Populate all_details from cache
        all_details = [get_item_details(x) for x in items]
        cache_keys = ['refeed:' + feed_url + ':' + x['guid'] for x in all_details]
        cached_contexts = [json.loads(x) if x else None for x in cache.mget(*cache_keys)]

        for item, cache_key, context, details in zip(items, cache_keys, cached_contexts, all_details):
            if context is None:
                resp = await session.get(details['link'])
                # XML can take a file-like object but aiohttp's read() isn't file-like
                article_tree = document_fromstring(await resp.read())
                context = build_item_context(article_tree)
                raw_context_to_save[cache_key] = json.dumps(context)

            # Re-write XML
            for k, v in context.items():
                node = item.find('./' + k)
                node.text = context[k]

    if raw_context_to_save:
        print('Saving: %d' % len(raw_context_to_save))
        cache.mset(raw_context_to_save)  # WISHLIST make this async

    return web.Response(text=ET.tostring(tree).decode('utf-8'), headers=pass_thru_headers)


app = web.Application()
app.router.add_get('/refeed/', refeed)

if not os.getenv('CI'):
    cache = redis.StrictRedis()  # TODO
    port = os.getenv('PORT', 8080)
    web.run_app(app, port=port)
