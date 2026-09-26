#!/usr/bin/env python3
# IRC Link Bot - Developed by acidvegas in Python (https://github.com/acidvegas/irclinkbot)
# parsers/threads.py

import html
import re

from fetch           import EMBED_UA, get_text
from formatting      import BLACK, CYAN, WHITE, clean, color, line, site_tag
from parsers.generic import meta_tags


TAG = site_tag('Threads', WHITE, BLACK)


async def page(session, match: re.Match) -> str | None:
	'''
	Parse a Threads post or profile link from its OpenGraph tags

	:param session: HTTP session
	:param match: Regex match of the Threads URL
	'''

	tags        = meta_tags(await get_text(session, match.group(0), headers={'User-Agent': EMBED_UA}))
	title       = html.unescape(tags.get('og:title', '')).split(' • Threads', 1)[0].removesuffix(' on Threads')
	description = html.unescape(tags.get('og:description', ''))

	if not title:
		return

	if match.group(1): # Post
		return line(TAG, color(clean(title, 80), CYAN) + ': ' + clean(description, 250))

	return line(TAG, color(clean(title, 80), CYAN), clean(description.split('. See the latest conversations', 1)[0], 200))


ROUTES = (
	(re.compile(r'https?://(?:www\.)?threads\.(?:net|com)/@[\w.]+(/post/[\w-]+)?/?(?:[?#].*)?$'), page),
)
