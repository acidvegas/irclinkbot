#!/usr/bin/env python3
# IRC Link Bot - Developed by acidvegas in Python (https://github.com/acidvegas/irclinkbot)
# parsers/hackernews.py

import re
import urllib.parse

from fetch      import get_json
from formatting import BLACK, CYAN, GREY, ORANGE, ago, bold, clean, color, line, site_tag, stat


TAG = site_tag('Hacker News', BLACK, ORANGE)
API = 'https://hacker-news.firebaseio.com/v0'


async def item(session, match: re.Match) -> str | None:
	'''
	Parse a Hacker News story, comment, or poll link using the public Firebase API

	:param session: HTTP session
	:param match: Regex match with the item id as group 1
	'''

	data = await get_json(session, f'{API}/item/{match.group(1)}.json')

	if data.get('type') == 'comment':
		return line(TAG, color(data.get('by', '[deleted]'), CYAN) + ': ' + clean(data.get('text', '[deleted]'), 250), color('comment', GREY), ago(data['time']))

	domain = urllib.parse.urlparse(data['url']).hostname.removeprefix('www.') if data.get('url') else None

	return line(TAG,
		bold(clean(data.get('title', ''), 250)) + (color(f' ({domain})', GREY) if domain else ''),
		stat(data.get('score', 0), 'points'),
		color(data.get('by', '[deleted]'), CYAN),
		stat(data.get('descendants', 0), 'comments'),
		ago(data['time'])
	)


async def user(session, match: re.Match) -> str | None:
	'''
	Parse a Hacker News user link

	:param session: HTTP session
	:param match: Regex match with the username as group 1
	'''

	data = await get_json(session, f'{API}/user/{match.group(1)}.json')

	return line(TAG,
		color(data['id'], CYAN),
		clean(data['about'], 150) if data.get('about') else None,
		stat(data.get('karma', 0), 'karma'),
		color('joined ', GREY) + ago(data['created'])
	)


ROUTES = (
	(re.compile(r'https?://news\.ycombinator\.com/item\?(?:.*&)?id=(\d+)'),  item),
	(re.compile(r'https?://news\.ycombinator\.com/user\?(?:.*&)?id=([\w-]+)'), user),
)
