#!/usr/bin/env python3
# IRC Link Bot - Developed by acidvegas in Python (https://github.com/acidvegas/irclinkbot)
# parsers/twitch.py

import datetime
import re

from fetch      import get_json
from formatting import CYAN, GREY, PURPLE, RED, WHITE, ago, bold, clean, color, duration, line, runtime, site_tag, stat, timestamp


TAG     = site_tag('Twitch', WHITE, PURPLE)
API     = 'https://gql.twitch.tv/gql'
HEADERS = {'Client-ID': 'kimne78kx3ncx6brgo4mv6wki5h1ko'} # Public client id used by the twitch.tv website itself, not a personal API key



async def channel(session, match: re.Match) -> str | None:
	'''
	Parse a Twitch channel link

	:param session: HTTP session
	:param match: Regex match with the channel login as group 1
	'''

	query = 'query($login:String!){user(login:$login){displayName description followers{totalCount} stream{title viewersCount createdAt game{name}} lastBroadcast{title game{name}}}}'
	user  = (await get_json(session, API, headers=HEADERS, json={'query': query, 'variables': {'login': match.group(1)}}))['data']['user']

	if not user:
		return

	if stream := user.get('stream'):
		return line(TAG,
			color(user['displayName'], CYAN) + ' ' + color('LIVE', RED),
			bold(clean(stream['title'], 200)),
			(stream.get('game') or {}).get('name'),
			stat(stream.get('viewersCount', 0), 'viewers'),
			color('up ' + duration(datetime.datetime.now(datetime.UTC).timestamp() - timestamp(stream['createdAt'])), GREY)
		)

	last = user.get('lastBroadcast') or {}

	return line(TAG,
		color(user['displayName'], CYAN) + ' ' + color('offline', GREY),
		clean(user.get('description') or '', 150),
		stat(user['followers']['totalCount'], 'followers'),
		color('last: ', GREY) + clean(last['title'], 100) if last.get('title') else None
	)


async def clip(session, match: re.Match) -> str | None:
	'''
	Parse a Twitch clip link

	:param session: HTTP session
	:param match: Regex match with the clip slug as group 1
	'''

	query = 'query($slug:ID!){clip(slug:$slug){title viewCount durationSeconds createdAt broadcaster{displayName} curator{displayName} game{name}}}'
	data  = (await get_json(session, API, headers=HEADERS, json={'query': query, 'variables': {'slug': match.group(1)}}))['data']['clip']

	if not data:
		return

	return line(TAG,
		bold(clean(data['title'], 200)),
		color((data.get('broadcaster') or {}).get('displayName', ''), CYAN),
		(data.get('game') or {}).get('name'),
		runtime(data.get('durationSeconds', 0)),
		stat(data.get('viewCount', 0), 'views'),
		color('clipped by ' + data['curator']['displayName'], GREY) if data.get('curator') else None,
		ago(timestamp(data['createdAt']))
	)


async def video(session, match: re.Match) -> str | None:
	'''
	Parse a Twitch VOD link

	:param session: HTTP session
	:param match: Regex match with the video id as group 1
	'''

	query = 'query($id:ID!){video(id:$id){title lengthSeconds viewCount createdAt owner{displayName} game{name}}}'
	data  = (await get_json(session, API, headers=HEADERS, json={'query': query, 'variables': {'id': match.group(1)}}))['data']['video']

	if not data:
		return

	return line(TAG,
		bold(clean(data['title'], 200)),
		color((data.get('owner') or {}).get('displayName', ''), CYAN),
		(data.get('game') or {}).get('name'),
		runtime(data.get('lengthSeconds', 0)),
		stat(data.get('viewCount', 0), 'views'),
		ago(timestamp(data['createdAt']))
	)


ROUTES = (
	(re.compile(r'https?://(?:www\.|m\.)?twitch\.tv/videos/(\d+)'),                           video),
	(re.compile(r'https?://clips\.twitch\.tv/(?:embed\?clip=)?([\w-]+)'),                     clip),
	(re.compile(r'https?://(?:www\.|m\.)?twitch\.tv/\w+/clip/([\w-]+)'),                      clip),
	(re.compile(r'https?://(?:www\.|m\.)?twitch\.tv/(?!directory|downloads|jobs|p/|settings|search)(\w+)/?(?:[?#].*)?$'), channel),
)
