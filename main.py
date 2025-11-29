import json
import logging
import os
from typing import Any
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


def build_item_context(tree: HtmlElement) -> dict[str, str]:
    """
    Build the context needed to replace item fields
    """
    data: dict[str, str] = {"description": ""}

    jsonld_elem = tree.find('./head/script[@type="application/ld+json"]')
    if jsonld_elem is not None and jsonld_elem.text is not None:
        jsonld: dict[str, Any] | list[Any] = json.loads(jsonld_elem.text)

        # Handle JSON-LD that might be a list or have @graph
        if isinstance(jsonld, list):
            jsonld = jsonld[0] if jsonld else {}
        elif "@graph" in jsonld:
            # Find WebPage type in graph, or fall back to first item with description/thumbnailUrl
            graph = jsonld["@graph"]
            jsonld = {}
            for item in graph:
                if item.get("@type") == "WebPage" and "description" in item:
                    jsonld = item
                    break
            # Fallback to first item with thumbnailUrl if no WebPage found
            if not jsonld:
                for item in graph:
                    if "thumbnailUrl" in item:
                        jsonld = item
                        break
            # Last resort: use first item
            if not jsonld and graph:
                jsonld = graph[0]

        if "description" not in jsonld:
            description_meta = tree.find('./head/meta[@name="description"]')
            if description_meta is not None:
                jsonld["description"] = description_meta.get("content")

        # Build description HTML, conditionally including thumbnail if present
        description_text = jsonld.get("description", "")
        thumbnail_url = jsonld.get("thumbnailUrl")

        if thumbnail_url:
            data["description"] = f"""
<img src="{thumbnail_url}" width="300" style="float: left; margin-right: 5px; max-width: 100%;" />
<p>{description_text}</p>
"""
        else:
            data["description"] = f"<p>{description_text}</p>"

    return data


@alru_cache(maxsize=CACHE_SIZE)
async def fetch_seo_context(url: str, guid: str) -> dict[str, str]:
    logger.info("Fetching url: %s guid: %s", url, guid)
    async with aiohttp.ClientSession() as session:  # TODO headers=
        resp = await session.get(url, timeout=aiohttp.ClientTimeout(total=5))
        resp.raise_for_status()
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
            resp = await session.get(feed_url, timeout=aiohttp.ClientTimeout(total=5))
            resp.raise_for_status()
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
