#!/usr/bin/env python3
# IRC Link Bot - Developed by acidvegas in Python (https://github.com/acidvegas/irclinkbot)
# parsers/soundcloud.py

import json
import re

from fetch      import get_text
from formatting import BLACK, CYAN, GREY, ORANGE, ago, bold, clean, color, line, runtime, site_tag, stat, timestamp


TAG = site_tag('SoundCloud', ORANGE, BLACK)


async def page(session, match: re.Match) -> str | None:
	'''
	Parse a SoundCloud track, playlist, or user link from the page's embedded hydration data

	:param session: HTTP session
	:param match: Regex match of the SoundCloud URL
	'''

	text = await get_text(session, match.group(0))

	if not (data := re.search(r'window\.__sc_hydration = (\[.*?\]);</script>', text, re.S)):
		return

	hydration = {item['hydratable']: item['data'] for item in json.loads(data.group(1)) if isinstance(item.get('data'), dict)}

	if sound := hydration.get('sound') or hydration.get('playlist'):
		user  = sound.get('user') or hydration.get('user', {})
		stamp = timestamp(sound['created_at']) if sound.get('created_at') else None
		return line(TAG,
			bold(clean(sound['title'], 150)),
			color(clean(user.get('username', ''), 50), CYAN),
			stat(sound['track_count'], 'tracks') if 'track_count' in sound else None,
			runtime(sound.get('duration', 0) // 1000),
			stat(sound['playback_count'], 'plays') if sound.get('playback_count') is not None else None,
			stat(sound.get('likes_count') or 0, 'likes'),
			stat(sound['comment_count'], 'comments') if sound.get('comment_count') is not None else None,
			color(sound['genre'], GREY) if sound.get('genre') else None,
			ago(stamp) if stamp else None
		)

	if user := hydration.get('user'):
		return line(TAG,
			color(clean(user.get('username', ''), 50), CYAN),
			clean(user.get('description') or '', 150),
			stat(user.get('followers_count', 0), 'followers'),
			stat(user.get('track_count', 0), 'tracks')
		)


ROUTES = (
	(re.compile(r'https?://(?:www\.|m\.)?soundcloud\.com/(?!discover|search|upload|stream|you/|pages/)[\w-]+(?:/[\w-]+){0,2}/?(?:[?#].*)?$'), page),
)
