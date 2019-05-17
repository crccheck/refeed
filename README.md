Refeed
======

[![Build Status](https://travis-ci.org/crccheck/refeed.svg?branch=master)](https://travis-ci.org/crccheck/refeed)

Re-create an RSS feed based on SEO/Social media metadata.

RSS feeds for many sites exist, but little effort is made to design them.
However, a lot of effort is put into adding metadata for SEO and social media.
This takes an existing RSS feed and re-creates it using social media metadata.


Environment Configuration
-------------------------

* `CACHE_SIZE` -- (default: 500) How many articles to keep cached. Should be about 30 * number_of_feeds


Example
-------

```
docker run --rm -it -p 8080:8080 crccheck/refeed
```

Then compare:
* https://www.architecturaldigest.com/feed/rss
* http://localhost:8080/refeed/?feed=https://www.architecturaldigest.com/feed/rss
