#!/usr/bin/env python3
# IRC Link Bot - Developed by acidvegas in Python (https://github.com/acidvegas/irclinkbot)
# parsers/wayback.py

import re
import urllib.parse

from fetch           import fetch
from formatting      import BLACK, GREY, WHITE, bold, color, line, site_tag
from parsers.generic import page_title


TAG = site_tag('Wayback Machine', WHITE, BLACK)


async def snapshot(session, match: re.Match) -> str | None:
	'''
	Parse a Wayback Machine snapshot link: the archived page title, original site & snapshot date

	:param session: HTTP session
	:param match: Regex match with the timestamp as group 1 & original URL as group 2
	'''

	stamp, original = match.groups()
	response        = await fetch(session, match.group(0))
	title           = page_title(response) if 'html' in response.content_type and response.status < 400 else None
	date            = f'{stamp[:4]}-{stamp[4:6] or "01"}-{stamp[6:8] or "01"}'

	return line(TAG,
		bold(title) if title else None,
		color((urllib.parse.urlparse(original if '://' in original else 'http://' + original).hostname or original).removeprefix('www.'), GREY),
		color('archived ' + date, GREY)
	)


ROUTES = (
	(re.compile(r'https?://web\.archive\.org/web/(\d{4,14})\w*/(\S+)'), snapshot),
)
