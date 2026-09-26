#!/usr/bin/env python3
# IRC Link Bot - Developed by acidvegas in Python (https://github.com/acidvegas/irclinkbot)
# parsers/amazon.py

import re

from fetch      import get_text
from formatting import BLACK, GREY, YELLOW, bold, clean, color, line, site_tag


TAG = site_tag('Amazon', YELLOW, BLACK)


async def product(session, match: re.Match) -> str | None:
	'''
	Parse an Amazon product link by scraping the product page (Amazon may serve a captcha instead)

	:param session: HTTP session
	:param match: Regex match with the domain as group 1 & ASIN as group 2
	'''

	page = await get_text(session, f'https://www.{match.group(1)}/dp/{match.group(2)}', headers={'Accept': 'text/html'})

	if not (title := re.search(r'id="productTitle"[^>]*>(.*?)</span>', page, re.S)):
		return

	price   = re.search(r'class="a-price[^"]*priceToPay[^"]*".{0,300}?a-price-symbol">([^<]*)<.{0,100}?a-price-whole">([\d,.]+?)<.{0,100}?a-price-fraction">(\d+)<', page, re.S)
	rating  = re.search(r'([\d.]+) out of 5 stars', page)
	reviews = re.search(r'id="acrCustomerReviewText"[^>]*>([^<]+)<', page)

	return line(TAG,
		bold(clean(title.group(1), 200)),
		'{}{}.{}'.format(*price.groups()) if price else None,
		f'{rating.group(1)}/5' + (color(f' ({clean(reviews.group(1), 30).strip("()")} ratings)', GREY) if reviews else '') if rating else None
	)


ROUTES = (
	(re.compile(r'https?://(?:www\.|smile\.)?(amazon\.(?:com|ca|co\.uk|de|fr|it|es|nl|se|pl|com\.au|com\.mx|com\.br|co\.jp|in))/(?:.*/)?(?:dp|gp/product|gp/aw/d)/(\w{10})'), product),
)
