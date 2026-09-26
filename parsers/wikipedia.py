#!/usr/bin/env python3
# IRC Link Bot - Developed by acidvegas in Python (https://github.com/acidvegas/irclinkbot)
# parsers/wikipedia.py

import re

from fetch      import BOT_UA, get_json
from formatting import BLACK, GREY, WHITE, bold, clean, color, line, site_tag


TAG = site_tag('Wikipedia', BLACK, WHITE)


async def article(session, match: re.Match) -> str | None:
	'''
	Parse a Wikipedia article link using the REST summary API (Wikimedia asks for an identifying User-Agent)

	:param session: HTTP session
	:param match: Regex match with the language as group 1 & article title as group 2
	'''

	lang, title = match.groups()
	data        = await get_json(session, f'https://{lang}.wikipedia.org/api/rest_v1/page/summary/{title}', headers={'User-Agent': BOT_UA})

	return line(TAG,
		bold(clean(data['title'], 100)) + (color(f' ({clean(data["description"], 80)})', GREY) if data.get('description') else ''),
		clean(data.get('extract', ''), 250)
	)


ROUTES = (
	(re.compile(r'https?://(\w+)(?:\.m)?\.wikipedia\.org/wiki/([^?#\s]+)'), article),
)
