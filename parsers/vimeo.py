#!/usr/bin/env python3
# IRC Link Bot - Developed by acidvegas in Python (https://github.com/acidvegas/irclinkbot)
# parsers/vimeo.py

import re

from fetch      import get_json
from formatting import CYAN, GREY, LIGHTCYAN, WHITE, bold, clean, color, line, runtime, site_tag, stat


TAG = site_tag('Vimeo', WHITE, LIGHTCYAN)


async def video(session, match: re.Match) -> str | None:
	'''
	Parse a Vimeo video link using the public simple API, falling back to oEmbed

	:param session: HTTP session
	:param match: Regex match with the video id as group 1
	'''

	try:
		data = (await get_json(session, f'https://vimeo.com/api/v2/video/{match.group(1)}.json'))[0]
	except Exception:
		data = await get_json(session, f'https://vimeo.com/api/oembed.json?url=https://vimeo.com/{match.group(1)}')
		return line(TAG, bold(clean(data['title'], 200)), color(clean(data.get('author_name', ''), 50), CYAN), runtime(data.get('duration', 0)))

	return line(TAG,
		bold(clean(data['title'], 200)),
		color(clean(data.get('user_name', ''), 50), CYAN),
		runtime(data.get('duration', 0)),
		stat(data['stats_number_of_plays'], 'plays') if data.get('stats_number_of_plays') else None,
		stat(data['stats_number_of_likes'], 'likes') if data.get('stats_number_of_likes') else None,
		color(data['upload_date'][:10], GREY) if data.get('upload_date') else None
	)


ROUTES = (
	(re.compile(r'https?://(?:www\.|player\.)?vimeo\.com/(?:video/|channels/[\w-]+/|groups/[\w-]+/videos/)?(\d+)'), video),
)
