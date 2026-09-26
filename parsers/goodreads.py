#!/usr/bin/env python3
# IRC Link Bot - Developed by acidvegas in Python (https://github.com/acidvegas/irclinkbot)
# parsers/goodreads.py

import re

from fetch           import get_text
from formatting      import BROWN, CYAN, GREY, WHITE, bold, clean, color, line, number, site_tag
from parsers.generic import json_ld


TAG = site_tag('Goodreads', WHITE, BROWN)


async def book(session, match: re.Match) -> str | None:
	'''
	Parse a Goodreads book link from the page's JSON-LD data

	:param session: HTTP session
	:param match: Regex match with the book id as group 1
	'''

	if not (data := json_ld(await get_text(session, f'https://www.goodreads.com/book/show/{match.group(1)}'), 'Book')):
		return

	rating  = data.get('aggregateRating') or {}
	authors = data.get('author') or []

	return line(TAG,
		bold(clean(data['name'], 150)),
		color(', '.join(clean(author['name'], 40) for author in authors[:2]), CYAN) if authors else None,
		f'{float(rating["ratingValue"]):.2f}/5 ' + color(f'({number(rating.get("ratingCount", 0))} ratings)', GREY) if rating.get('ratingValue') else None,
		f'{data["numberOfPages"]} ' + color('pages', GREY) if data.get('numberOfPages') else None
	)


ROUTES = (
	(re.compile(r'https?://(?:www\.)?goodreads\.com/(?:en/)?book/show/(\d+)'), book),
)
