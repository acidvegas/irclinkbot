#!/usr/bin/env python3
# IRC Link Bot - Developed by acidvegas in Python (https://github.com/acidvegas/irclinkbot)
# parsers/reddit.py

import re

from fetch      import BOT_UA, get_json
from formatting import CYAN, GREY, ORANGE, WHITE, ago, bold, clean, color, line, site_tag, stat


TAG     = site_tag('Reddit', WHITE, ORANGE)
HEADERS = {'User-Agent': BOT_UA}


async def post(session, match: re.Match) -> str | None:
	'''
	Parse a Reddit post link using the public JSON endpoint, falling back to oEmbed when Reddit blocks the request

	:param session: HTTP session
	:param match: Regex match with the post id as group 1
	'''

	post_id = match.group(1)

	try:
		data = (await get_json(session, f'https://www.reddit.com/comments/{post_id}.json?limit=1', headers=HEADERS))[0]['data']['children'][0]['data']
	except Exception:
		data = await get_json(session, f'https://www.reddit.com/oembed?url=https://www.reddit.com/r/all/comments/{post_id}/', headers=HEADERS)
		sub  = re.search(r'reddit\.com/r/(\w+)/', data.get('html', ''))
		return line(TAG, (color(f'r/{sub.group(1)}', GREY) + ' ' if sub else '') + bold(clean(data['title'], 250)), color(f'u/{data["author_name"]}', CYAN))

	return line(TAG,
		color(f'r/{data["subreddit"]}', GREY) + ' ' + bold(clean(data['title'], 250)),
		color(clean(data['link_flair_text'], 30), GREY) if data.get('link_flair_text') else None,
		color(f'u/{data["author"]}', CYAN),
		stat(data.get('score', 0), 'points') + color(f' ({int(data.get("upvote_ratio", 0) * 100)}%)', GREY),
		stat(data.get('num_comments', 0), 'comments'),
		ago(data['created_utc']),
		nsfw=bool(data.get('over_18'))
	)


async def subreddit(session, match: re.Match) -> str | None:
	'''
	Parse a subreddit link

	:param session: HTTP session
	:param match: Regex match with the subreddit name as group 1
	'''

	data = (await get_json(session, f'https://www.reddit.com/r/{match.group(1)}/about.json', headers=HEADERS))['data']

	return line(TAG,
		bold(f'r/{data["display_name"]}'),
		clean(data.get('public_description') or data.get('title', ''), 200),
		stat(data.get('subscribers', 0), 'members'),
		ago(data['created_utc']),
		nsfw=bool(data.get('over18'))
	)


async def user(session, match: re.Match) -> str | None:
	'''
	Parse a Reddit user link

	:param session: HTTP session
	:param match: Regex match with the username as group 1
	'''

	data = (await get_json(session, f'https://www.reddit.com/user/{match.group(1)}/about.json', headers=HEADERS))['data']

	return line(TAG,
		color(f'u/{data["name"]}', CYAN),
		stat(data.get('link_karma', 0), 'post karma'),
		stat(data.get('comment_karma', 0), 'comment karma'),
		color('joined ', GREY) + ago(data['created_utc'])
	)


ROUTES = (
	(re.compile(r'https?://(?:(?:www|old|new|np|m|sh)\.)?reddit\.com/(?:r/\w+/)?comments/(\w+)'), post),
	(re.compile(r'https?://(?:www\.)?redd\.it/(\w+)/?(?:[?#].*)?$'),                           post),
	(re.compile(r'https?://(?:(?:www|old|new|np|m)\.)?reddit\.com/r/(\w+)/?(?:[?#].*)?$'),     subreddit),
	(re.compile(r'https?://(?:(?:www|old|new|np|m)\.)?reddit\.com/u(?:ser)?/([\w-]+)/?(?:[?#].*)?$'), user),
)
