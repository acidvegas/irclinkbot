#!/usr/bin/env python3
# IRC Link Bot - Developed by acidvegas in Python (https://github.com/acidvegas/irclinkbot)
# parsers/bandcamp.py

import re

from fetch           import get_text
from formatting      import CYAN, GREY, LIGHTCYAN, WHITE, bold, clean, color, line, runtime, site_tag, stat
from parsers.generic import json_ld


TAG = site_tag('Bandcamp', WHITE, LIGHTCYAN)


async def release(session, match: re.Match) -> str | None:
	'''
	Parse a Bandcamp album or track link from the page's JSON-LD data

	:param session: HTTP session
	:param match: Regex match of the Bandcamp URL
	'''

	page = await get_text(session, match.group(0))

	if not (data := json_ld(page, 'MusicAlbum') or json_ld(page, 'MusicRecording')):
		return

	artist = (data.get('byArtist') or {}).get('name', '')
	year   = re.search(r'\b(\d{4})\b', data.get('datePublished', ''))
	length = re.match(r'P(\d+)H(\d+)M(\d+)S', data.get('duration', ''))

	return line(TAG,
		bold(clean(data['name'], 150)),
		color(clean(artist, 60), CYAN),
		stat(data['numTracks'], 'tracks') if data.get('numTracks') else None,
		runtime(int(length.group(1)) * 3600 + int(length.group(2)) * 60 + int(length.group(3))) if length else None,
		color(year.group(1), GREY) if year else None
	)


ROUTES = (
	(re.compile(r'https?://[\w-]+\.bandcamp\.com/(?:album|track)/[\w-]+'), release),
)
