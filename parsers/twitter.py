#!/usr/bin/env python3
# IRC Link Bot - Developed by acidvegas in Python (https://github.com/acidvegas/irclinkbot)
# parsers/twitter.py

import re

from fetch      import get_json
from formatting import BLACK, CYAN, GREY, WHITE, ago, clean, color, line, site_tag, stat


TAG      = site_tag('X', WHITE, BLACK)
RESERVED = ('compose', 'explore', 'hashtag', 'home', 'i', 'intent', 'messages', 'notifications', 'search', 'settings', 'share', 'tos', 'privacy')


async def profile(session, match: re.Match) -> str | None:
	'''
	Parse an X/Twitter profile link using the FxTwitter API (no API key required)

	:param session: HTTP session
	:param match: Regex match with the username as group 1
	'''

	if match.group(1).lower() in RESERVED:
		return

	user = (await get_json(session, f'https://api.fxtwitter.com/{match.group(1)}'))['user']

	return line(TAG,
		color(clean(user['name'], 50), CYAN) + color(f' (@{user["screen_name"]})', GREY),
		clean(user.get('description', ''), 150),
		stat(user.get('followers', 0), 'followers'),
		stat(user.get('tweets', 0), 'tweets'),
		color('joined ' + user['joined'][-4:], GREY) if user.get('joined') else None
	)


async def status(session, match: re.Match) -> str | None:
	'''
	Parse an X/Twitter status link using the FxTwitter API (no API key required)

	:param session: HTTP session
	:param match: Regex match with the username as group 1 & status id as group 2
	'''

	tweet  = (await get_json(session, f'https://api.fxtwitter.com/{match.group(1)}/status/{match.group(2)}'))['tweet']
	author = tweet['author']
	media  = tweet.get('media') or {}
	counts = [f'{len(media[kind])} {kind[:-1] if len(media[kind]) == 1 else kind}' for kind in ('photos', 'videos') if media.get(kind)]
	text   = clean(tweet.get('text', ''), 220)

	if quote := tweet.get('quote'):
		text += color(f' [quoting @{quote["author"]["screen_name"]}: {clean(quote.get("text", ""), 80)}]', GREY)

	return line(TAG,
		color(clean(author['name'], 50), CYAN) + color(f' (@{author["screen_name"]})', GREY) + ': ' + text,
		stat(tweet.get('replies', 0), 'replies'),
		stat(tweet.get('retweets', 0), 'RTs'),
		stat(tweet.get('likes', 0), 'likes'),
		stat(tweet['views'], 'views') if tweet.get('views') else None,
		color(', '.join(counts), GREY) if counts else None,
		ago(tweet['created_timestamp']) if tweet.get('created_timestamp') else None,
		nsfw=bool(tweet.get('possibly_sensitive'))
	)


ROUTES = (
	(re.compile(r'https?://(?:www\.|mobile\.)?(?:twitter|x|fxtwitter|vxtwitter|fixupx|fixvx|twittpr)\.com/(\w{1,15})/status(?:es)?/(\d+)'), status),
	(re.compile(r'https?://(?:www\.|mobile\.)?(?:twitter|x)\.com/(\w{1,15})/?(?:[?#].*)?$'),                                        profile),
)
