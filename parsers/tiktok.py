#!/usr/bin/env python3
# IRC Link Bot - Developed by acidvegas in Python (https://github.com/acidvegas/irclinkbot)
# parsers/tiktok.py

import json
import re

from fetch      import get_text
from formatting import BLACK, CYAN, GREY, LIGHTCYAN, ago, clean, color, line, runtime, site_tag, stat


TAG = site_tag('TikTok', LIGHTCYAN, BLACK)


async def video(session, match: re.Match) -> str | None:
	'''
	Parse a TikTok video link from the page's embedded rehydration data

	:param session: HTTP session
	:param match: Regex match with the username as group 1 & video id as group 2
	'''

	page = await get_text(session, f'https://www.tiktok.com/@{match.group(1)}/video/{match.group(2)}')

	if not (data := re.search(r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__"[^>]*>(.*?)</script>', page, re.S)):
		return

	item   = json.loads(data.group(1))['__DEFAULT_SCOPE__']['webapp.video-detail']['itemInfo']['itemStruct']
	author = item.get('author', {})
	stats  = item.get('stats', {})

	return line(TAG,
		color(clean(author.get('nickname') or author.get('uniqueId', ''), 50), CYAN) + color(f' (@{author.get("uniqueId", "")})', GREY) + ': ' + clean(item.get('desc', ''), 200),
		runtime(item.get('video', {}).get('duration', 0)),
		stat(stats.get('playCount', 0), 'views'),
		stat(stats.get('diggCount', 0), 'likes'),
		stat(stats.get('commentCount', 0), 'comments'),
		stat(stats.get('shareCount', 0), 'shares'),
		ago(int(item['createTime'])) if item.get('createTime') else None
	)


ROUTES = (
	(re.compile(r'https?://(?:www\.|m\.)?tiktok\.com/@([\w.-]+)/(?:video|photo)/(\d+)'), video),
)
