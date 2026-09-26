#!/usr/bin/env python3
# IRC Link Bot - Developed by acidvegas in Python (https://github.com/acidvegas/irclinkbot)
# parsers/__init__.py

import logging

from fetch   import fetch
from parsers import amazon, apple, arxiv, bandcamp, bluesky, cve, dailymotion, discord, dockerhub, ebay, etsy, fourchan, generic, gitea, github, gitlab, goodreads, hackernews, huggingface, imdb, imgur, instagram, kick, lemmy, letterboxd, lobsters, mastodon, packages, reddit, soundcloud, spotify, steam, telegram, threads, tiktok, twitch, twitter, vimeo, wayback, wikipedia, youtube


THEMED = (wayback, youtube, twitter, reddit, bluesky, threads, github, gitea, gitlab, hackernews, lobsters, packages, dockerhub, cve, arxiv, huggingface, wikipedia, twitch, kick, vimeo, dailymotion, imgur, spotify, apple, soundcloud, bandcamp, instagram, tiktok, discord, telegram, fourchan, steam, imdb, letterboxd, goodreads, amazon, ebay, etsy, mastodon, lemmy) # Order matters, first matching route wins (broad fediverse patterns last)


async def parse(session, url: str) -> str | None:
	'''
	Parse a link into an output line, using a themed parser when one matches (also after redirects), otherwise the generic parser

	:param session: HTTP session
	:param url: URL to parse
	'''

	if result := await themed(session, url):
		return result

	response = await fetch(session, url)

	if response.url != url and (result := await themed(session, response.url)):
		return result

	return generic.parse(response)


async def themed(session, url: str) -> str | None:
	'''
	Run the first themed parser whose route matches the URL

	:param session: HTTP session
	:param url: URL to parse
	'''

	for module in THEMED:
		for pattern, handler in module.ROUTES:
			if match := pattern.match(url):
				try:
					return await handler(session, match)
				except Exception as ex:
					logging.warning(f'{module.__name__} failed on {url}: {ex.__class__.__name__}: {ex}')
					return
