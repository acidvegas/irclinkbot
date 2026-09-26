#!/usr/bin/env python3
# IRC Link Bot - Developed by acidvegas in Python (https://github.com/acidvegas/irclinkbot)
# parsers/bluesky.py

import re

from fetch      import get_json
from formatting import CYAN, GREY, LIGHTBLUE, WHITE, ago, clean, color, line, site_tag, stat, timestamp


TAG         = site_tag('Bluesky', WHITE, LIGHTBLUE)
API         = 'https://public.api.bsky.app/xrpc'
NSFW_LABELS = ('porn', 'sexual', 'nudity', 'graphic-media')


async def post(session, match: re.Match) -> str | None:
	'''
	Parse a Bluesky post link using the public AppView API (no API key required)

	:param session: HTTP session
	:param match: Regex match with the handle/DID as group 1 & record key as group 2
	'''

	data   = await get_json(session, f'{API}/app.bsky.feed.getPostThread?depth=0&parentHeight=0&uri=at://{match.group(1)}/app.bsky.feed.post/{match.group(2)}')
	item   = data['thread']['post']
	author = item['author']
	record = item['record']
	stamp  = timestamp(record['createdAt']) if record.get('createdAt') else None
	labels = [label['val'] for label in item.get('labels', [])]

	return line(TAG,
		color(clean(author.get('displayName') or author['handle'], 50), CYAN) + color(f' (@{author["handle"]})', GREY) + ': ' + clean(record.get('text', ''), 220),
		stat(item.get('replyCount', 0), 'replies'),
		stat(item.get('repostCount', 0), 'reposts'),
		stat(item.get('likeCount', 0), 'likes'),
		ago(stamp) if stamp else None,
		nsfw=any(label in NSFW_LABELS for label in labels)
	)


async def profile(session, match: re.Match) -> str | None:
	'''
	Parse a Bluesky profile link using the public AppView API (no API key required)

	:param session: HTTP session
	:param match: Regex match with the handle/DID as group 1
	'''

	user = await get_json(session, f'{API}/app.bsky.actor.getProfile?actor={match.group(1)}')

	return line(TAG,
		color(clean(user.get('displayName') or user['handle'], 50), CYAN) + color(f' (@{user["handle"]})', GREY),
		clean(user.get('description', ''), 150),
		stat(user.get('followersCount', 0), 'followers'),
		stat(user.get('postsCount', 0), 'posts')
	)


ROUTES = (
	(re.compile(r'https?://(?:www\.)?bsky\.app/profile/([\w.:-]+)/post/(\w+)'), post),
	(re.compile(r'https?://(?:www\.)?bsky\.app/profile/([\w.:-]+)/?(?:[?#].*)?$'), profile),
)
