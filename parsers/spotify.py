#!/usr/bin/env python3
# IRC Link Bot - Developed by acidvegas in Python (https://github.com/acidvegas/irclinkbot)
# parsers/spotify.py

import re

from fetch           import EMBED_UA, get_text
from formatting      import BLACK, LIGHTGREEN, bold, clean, line, site_tag
from parsers.generic import meta_tags


TAG = site_tag('Spotify', BLACK, LIGHTGREEN)


async def item(session, match: re.Match) -> str | None:
	'''
	Parse a Spotify track, album, artist, playlist, episode, or show link from its OpenGraph tags

	:param session: HTTP session
	:param match: Regex match with the item type as group 1 & id as group 2
	'''

	tags = meta_tags(await get_text(session, f'https://open.spotify.com/{match.group(1)}/{match.group(2)}', headers={'User-Agent': EMBED_UA}))

	if not tags.get('og:title'):
		return

	return line(TAG, bold(clean(tags['og:title'].removesuffix(' | Spotify'), 150)), clean(tags.get('og:description', ''), 200))


ROUTES = (
	(re.compile(r'https?://open\.spotify\.com/(?:intl-\w+/)?(track|album|artist|playlist|episode|show)/(\w+)'), item),
)
