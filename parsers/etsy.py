#!/usr/bin/env python3
# IRC Link Bot - Developed by acidvegas in Python (https://github.com/acidvegas/irclinkbot)
# parsers/etsy.py

import re

from fetch           import get_text
from formatting      import CYAN, GREY, ORANGE, WHITE, bold, clean, color, line, number, site_tag
from parsers.generic import json_ld


TAG = site_tag('Etsy', WHITE, ORANGE)


async def listing(session, match: re.Match) -> str | None:
	'''
	Parse an Etsy listing link from the page's JSON-LD data (Etsy may block the request)

	:param session: HTTP session
	:param match: Regex match with the listing id as group 1
	'''

	if not (data := json_ld(await get_text(session, f'https://www.etsy.com/listing/{match.group(1)}', headers={'Accept': 'text/html'}), 'Product')):
		return

	offers = data.get('offers') or {}
	offers = offers[0] if isinstance(offers, list) and offers else offers
	price  = offers.get('price') or offers.get('lowPrice')
	rating = data.get('aggregateRating') or {}
	shop   = data.get('brand') or {}

	return line(TAG,
		bold(clean(data['name'], 200)),
		color(clean(shop.get('name', ''), 50), CYAN) if isinstance(shop, dict) and shop.get('name') else None,
		f'{price} {offers.get("priceCurrency", "")}'.strip() if price else None,
		f'{rating["ratingValue"]}/5 ' + color(f'({number(rating.get("reviewCount", 0))} reviews)', GREY) if rating.get('ratingValue') else None
	)


ROUTES = (
	(re.compile(r'https?://(?:www\.)?etsy\.com/(?:\w{2}/)?listing/(\d+)'), listing),
)
