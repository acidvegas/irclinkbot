#!/usr/bin/env python3
# IRC Link Bot - Developed by acidvegas in Python (https://github.com/acidvegas/irclinkbot)
# parsers/ebay.py

import html
import re

from fetch           import get_text
from formatting      import BLUE, GREY, WHITE, bold, clean, color, line, site_tag
from parsers.generic import meta_tags


TAG = site_tag('eBay', BLUE, WHITE)


async def item(session, match: re.Match) -> str | None:
	'''
	Parse an eBay listing link by scraping the listing page (eBay may block the request)

	:param session: HTTP session
	:param match: Regex match with the domain as group 1 & item id as group 2
	'''

	page      = await get_text(session, f'https://www.{match.group(1)}/itm/{match.group(2)}', headers={'Accept': 'text/html'})
	title     = re.search(r'class="x-item-title__mainTitle"[^>]*>\s*<span[^>]*>([^<]+)<', page) or re.search(r'(.+)', html.unescape(meta_tags(page).get('og:title', '')).removesuffix(' | eBay'))
	price     = re.search(r'class="x-price-primary"[^>]*>(?:\s*<[^>]+>)*\s*([^<]+)<', page)
	condition = re.search(r'class="x-item-condition-text"[^>]*>(?:\s*<[^>]+>)*\s*([^<]+)<', page)

	if not title:
		return

	return line(TAG,
		bold(clean(title.group(1), 200)),
		clean(price.group(1), 30) if price else None,
		color(clean(condition.group(1), 30), GREY) if condition else None
	)


ROUTES = (
	(re.compile(r'https?://(?:www\.|m\.)?(ebay\.(?:com|ca|co\.uk|de|fr|it|es|nl|com\.au|ie|at|ch|pl))/itm/(?:[\w-]+/)?(\d+)'), item),
)
