import json
import logging
import os
from xml.etree import ElementTree as ET

import aiohttp
import aiohttp.web_request
from aiohttp import web
from async_lru import alru_cache
from lxml.html import HtmlElement, document_fromstring

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


CACHE_SIZE = int(os.environ.get("CACHE_SIZE", 500))
DESCRIPTION_FMT = """
<img src="{thumbnailUrl}" width="300" style="float: left; margin-right: 5px; max-width: 100%;" />
<p>{description}</p>
""".format


def build_item_context(tree: HtmlElement) -> dict:
    """
    Build the context needed to replace item fields
    """
    data = {"description": ""}

    jsonld_elem = tree.find('./head/script[@type="application/ld+json"]')
    if jsonld_elem is not None:
        jsonld = json.loads(jsonld_elem.text)
        if "description" not in jsonld:
            description_meta = tree.find('./head/meta[@name="description"]')
            jsonld["description"] = description_meta.get("content")
        data["description"] = DESCRIPTION_FMT(**jsonld)

    return data


@alru_cache(maxsize=CACHE_SIZE)
async def fetch_seo_context(url: str, guid: str) -> dict:
    logger.info("Fetching url: %s guid: %s", url, guid)
    async with aiohttp.ClientSession() as session:  # TODO headers=
        resp = await session.get(url)
        # XML can take a file-like object but aiohttp's read() isn't file-like
        article_tree = document_fromstring(await resp.read())
        return build_item_context(article_tree)


async def refeed(request: aiohttp.web_request.Request) -> web.Response:
    try:
        feed_url = request.query["feed"]
    except KeyError:
        return web.Response(status=400, text="Must supply a ?feed=<rss url>")

    logger.info("Processing feed: %s", feed_url)

    async with aiohttp.ClientSession() as session:
        try:
            resp = await session.get(feed_url)
        except ValueError as e:
            return web.Response(status=400, text=str(e))

        tree = ET.fromstring(await resp.text())
        items = tree.findall(".//item")
        if not items:
            return web.Response(status=400, text="No feed items found")

        for item in items:
            link_elem = item.find("./link")
            guid_elem = item.find("./guid")

            if link_elem is None or link_elem.text is None:
                logger.warning("Skipping item with missing link")
                continue
            if guid_elem is None or guid_elem.text is None:
                logger.warning("Skipping item with missing guid")
                continue

            url = link_elem.text
            guid = guid_elem.text
            context = await fetch_seo_context(url, guid)

            # Re-write XML
            for k in context.keys():
                node = item.find("./" + k)
                assert node is not None
                node.text = context[k]

    logger.info(fetch_seo_context.cache_info())

    return web.Response(text=ET.tostring(tree).decode("utf-8"), content_type="application/rss+xml")


async def robotstxt(request: aiohttp.web_request.Request) -> web.Response:
    return web.Response(text="User-agent: *\nDisallow: /", content_type="text/plain")


app = web.Application()
app.router.add_get("/refeed/", refeed)
app.router.add_get("/robots.txt", robotstxt)

if not os.getenv("CI"):
    port = int(os.getenv("PORT", 8080))
    web.run_app(app, port=port)
