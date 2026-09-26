#!/usr/bin/env python3
# IRC Link Bot - Developed by acidvegas in Python (https://github.com/acidvegas/irclinkbot)
# parsers/gitlab.py

import re
import urllib.parse

from fetch      import get_json
from formatting import CYAN, GREEN, GREY, ORANGE, PURPLE, RED, WHITE, ago, bold, clean, color, line, site_tag, stat, timestamp


TAG      = site_tag('GitLab', WHITE, ORANGE)
API      = 'https://gitlab.com/api/v4'
RESERVED = ('dashboard', 'explore', 'groups', 'help', 'projects', 'search', 'users')


async def project(session, match: re.Match) -> str | None:
	'''
	Parse a GitLab project, issue, or merge request link using the public API

	:param session: HTTP session
	:param match: Regex match with the project path as group 1, item type as group 2 & item number as group 3
	'''

	path, kind, number = match.groups()

	if path.split('/', 1)[0].lower() in RESERVED:
		return

	encoded = urllib.parse.quote(path, safe='')

	if kind:
		data = await get_json(session, f'{API}/projects/{encoded}/{kind}/{number}')
		state = {'opened': color('open', GREEN), 'merged': color('merged', PURPLE)}.get(data['state'], color(data['state'], RED))
		label = 'MR !' if kind == 'merge_requests' else 'Issue #'
		return line(TAG,
			color(f'{path} {label}{number}', GREY) + ' ' + bold(clean(data['title'], 200)),
			state,
			color(data['author']['username'], CYAN),
			stat(data.get('user_notes_count', 0), 'comments'),
			ago(timestamp(data['created_at']))
		)

	data = await get_json(session, f'{API}/projects/{encoded}')

	return line(TAG,
		bold(data['path_with_namespace']),
		clean(data['description'], 150) if data.get('description') else None,
		stat(data.get('star_count', 0), 'stars'),
		stat(data.get('forks_count', 0), 'forks'),
		color('updated ', GREY) + ago(timestamp(data['last_activity_at'])) if data.get('last_activity_at') else None,
		color('archived', RED) if data.get('archived') else None
	)


ROUTES = (
	(re.compile(r'https?://gitlab\.com/([\w.-]+(?:/[\w.-]+)+?)(?:/-/(issues|merge_requests)/(\d+)|/-/.*|/?)(?:[?#].*)?$'), project),
)
