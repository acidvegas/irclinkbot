#!/usr/bin/env python3
# IRC Link Bot - Developed by acidvegas in Python (https://github.com/acidvegas/irclinkbot)
# parsers/lemmy.py

import re

from fetch      import get_json
from formatting import BLACK, CYAN, GREY, WHITE, ago, bold, clean, color, line, site_tag, stat, timestamp


TAG = site_tag('Lemmy', BLACK, WHITE)


async def post(session, match: re.Match) -> str | None:
	'''
	Parse a Lemmy post link using the instance's public API (no API key required)

	:param session: HTTP session
	:param match: Regex match with the host as group 1 & post id as group 2
	'''

	data = (await get_json(session, f'https://{match.group(1)}/api/v3/post?id={match.group(2)}'))['post_view']
	item = data['post']

	return line(TAG,
		color(f'!{data["community"]["name"]}', GREY) + ' ' + bold(clean(item['name'], 250)),
		color(data['creator']['name'], CYAN),
		stat(data['counts'].get('score', 0), 'points'),
		stat(data['counts'].get('comments', 0), 'comments'),
		ago(timestamp(item['published'])),
		nsfw=bool(item.get('nsfw') or data['community'].get('nsfw'))
	)


ROUTES = (
	(re.compile(r'https?://([\w.-]+\.[a-z]{2,})/post/(\d+)/?(?:[?#].*)?$'), post),
)
