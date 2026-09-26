#!/usr/bin/env python3
# IRC Link Bot - Developed by acidvegas in Python (https://github.com/acidvegas/irclinkbot)
# parsers/kick.py

import datetime
import re

from fetch      import get_json
from formatting import BLACK, CYAN, GREY, LIGHTGREEN, RED, bold, clean, color, duration, line, site_tag, stat, timestamp


TAG      = site_tag('Kick', BLACK, LIGHTGREEN)
RESERVED = ('browse', 'categories', 'category', 'following', 'search', 'video', 'terms-of-service', 'privacy-policy')


async def channel(session, match: re.Match) -> str | None:
	'''
	Parse a Kick channel link using the public channel API

	:param session: HTTP session
	:param match: Regex match with the channel slug as group 1
	'''

	if match.group(1).lower() in RESERVED:
		return

	data = await get_json(session, f'https://kick.com/api/v2/channels/{match.group(1)}')
	name = data['user']['username']

	if stream := data.get('livestream'):
		started = timestamp(stream['start_time'] or stream['created_at'])
		return line(TAG,
			color(name, CYAN) + ' ' + color('LIVE', RED),
			bold(clean(stream.get('session_title', ''), 200)),
			', '.join(category['name'] for category in stream.get('categories', [])[:2]) or None,
			stat(stream.get('viewer_count', 0), 'viewers'),
			color('up ' + duration(datetime.datetime.now(datetime.UTC).timestamp() - started), GREY),
			nsfw=bool(stream.get('is_mature'))
		)

	return line(TAG,
		color(name, CYAN) + ' ' + color('offline', GREY),
		clean(data['user'].get('bio') or '', 150),
		stat(data.get('followers_count', 0), 'followers')
	)


ROUTES = (
	(re.compile(r'https?://(?:www\.)?kick\.com/([\w-]+)/?(?:[?#].*)?$'), channel),
)
