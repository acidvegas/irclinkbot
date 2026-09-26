#!/usr/bin/env python3
# IRC Link Bot - Developed by acidvegas in Python (https://github.com/acidvegas/irclinkbot)
# parsers/apple.py

import re

from fetch      import get_json
from formatting import CYAN, GREY, PINK, PURPLE, WHITE, bold, clean, color, line, runtime, site_tag, stat


async def lookup(session, match: re.Match) -> str | None:
	'''
	Parse an Apple Music or Apple Podcasts link using the public iTunes lookup API

	:param session: HTTP session
	:param match: Regex match with the service as group 1, country as group 2, item id as group 3 & optional song id as group 4
	'''

	service, country, item_id, song_id = match.groups()
	results = (await get_json(session, f'https://itunes.apple.com/lookup?id={song_id or item_id}&country={country}'))['results']

	if not results:
		return

	data = results[0]
	year = color(data['releaseDate'][:4], GREY) if data.get('releaseDate') else None

	if service == 'podcasts':
		return line(site_tag('Apple Podcasts', WHITE, PURPLE),
			bold(clean(data.get('collectionName', ''), 150)),
			color(clean(data.get('artistName', ''), 60), CYAN),
			data.get('primaryGenreName'),
			stat(data.get('trackCount', 0), 'episodes')
		)

	tag = site_tag('Apple Music', WHITE, PINK)

	if data.get('wrapperType') == 'track':
		return line(tag,
			bold(clean(data['trackName'], 150)),
			color(clean(data.get('artistName', ''), 60), CYAN),
			clean(data.get('collectionName', ''), 80),
			runtime(data.get('trackTimeMillis', 0) // 1000),
			data.get('primaryGenreName'),
			year,
			nsfw=data.get('trackExplicitness') == 'explicit'
		)

	if data.get('wrapperType') == 'collection':
		return line(tag,
			bold(clean(data['collectionName'], 150)),
			color(clean(data.get('artistName', ''), 60), CYAN),
			stat(data.get('trackCount', 0), 'tracks'),
			data.get('primaryGenreName'),
			year,
			nsfw=data.get('collectionExplicitness') == 'explicit'
		)

	return line(tag, color(clean(data.get('artistName', ''), 60), CYAN), data.get('primaryGenreName'))


ROUTES = (
	(re.compile(r'https?://(music|podcasts)\.apple\.com/(\w{2})/(?:album|song|artist|podcast)/[^/]+/(?:id)?(\d+)(?:\?(?:.*&)?i=(\d+))?'), lookup),
)
