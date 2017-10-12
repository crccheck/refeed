import os

from aiohttp import web
import aiohttp


async def refeed(request):
    try:
        feed_url = request.GET['feed']
    except KeyError:
        return web.Response(status=400, text='Must supply a ?feed=<rss url>')

    try:
        async with aiohttp.ClientSession() as session:  # headers=
            resp = await session.get(feed_url)
            text = await resp.text()
        return web.Response(text=text)
    except ValueError as e:
        return web.Response(status=400, text=str(e))


app = web.Application()
app.router.add_get('/refeed/', refeed)

port = os.getenv('PORT', 8080)
web.run_app(app, port=port)
