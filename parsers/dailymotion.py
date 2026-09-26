#!/usr/bin/env python3
# IRC Link Bot - Developed by acidvegas in Python (https://github.com/acidvegas/irclinkbot)
# parsers/dailymotion.py

import re

from fetch      import get_json
from formatting import BLUE, CYAN, WHITE, ago, bold, clean, color, line, runtime, site_tag, stat


TAG    = site_tag('Dailymotion', WHITE, BLUE)
FIELDS = 'title,owner.screenname,duration,views_total,likes_total,created_time,explicit'


async def video(session, match: re.Match) -> str | None:
	'''
	Parse a Dailymotion video link using the public API

	:param session: HTTP session
	:param match: Regex match with the video id as group 1
	'''

	data = await get_json(session, f'https://api.dailymotion.com/video/{match.group(1)}?fields={FIELDS}')

	return line(TAG,
		bold(clean(data['title'], 200)),
		color(clean(data.get('owner.screenname', ''), 50), CYAN),
		runtime(data.get('duration', 0)),
		stat(data.get('views_total', 0), 'views'),
		stat(data['likes_total'], 'likes') if data.get('likes_total') is not None else None,
		ago(data['created_time']) if data.get('created_time') else None,
		nsfw=bool(data.get('explicit'))
	)


ROUTES = (
	(re.compile(r'https?://(?:www\.)?dailymotion\.com/video/(\w+)'), video),
	(re.compile(r'https?://(?:www\.)?dai\.ly/(\w+)'),                video),
)
