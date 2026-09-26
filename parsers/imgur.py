#!/usr/bin/env python3
# IRC Link Bot - Developed by acidvegas in Python (https://github.com/acidvegas/irclinkbot)
# parsers/imgur.py

import re

from fetch      import get_json
from formatting import GREEN, WHITE, ago, bold, clean, line, site_tag, stat, timestamp


TAG       = site_tag('Imgur', WHITE, GREEN)
CLIENT_ID = '546c25a59c58ad7' # Public client id used by the imgur.com website itself, not a personal API key


async def post(session, match: re.Match) -> str | None:
	'''
	Parse an Imgur post, album, or gallery link

	:param session: HTTP session
	:param match: Regex match with the post id as group 1
	'''

	data  = await get_json(session, f'https://api.imgur.com/post/v1/posts/{match.group(1)}?client_id={CLIENT_ID}&include=media')
	stamp = timestamp(data['created_at']) if data.get('created_at') else None

	return line(TAG,
		bold(clean(data.get('title') or 'Untitled', 200)),
		stat(data.get('image_count', 0), 'images'),
		stat(data.get('view_count', 0), 'views'),
		stat(data.get('upvote_count', 0), 'upvotes'),
		stat(data.get('comment_count', 0), 'comments'),
		ago(stamp) if stamp else None,
		nsfw=bool(data.get('is_mature'))
	)


ROUTES = (
	(re.compile(r'https?://(?:www\.|m\.)?imgur\.com/(?:gallery/|a/|t/\w+/)?(?:[\w-]*-)?(\w{5,8})/?(?:[?#].*)?$'), post),
)
