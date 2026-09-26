#!/usr/bin/env python3
# IRC Link Bot - Developed by acidvegas in Python (https://github.com/acidvegas/irclinkbot)
# parsers/huggingface.py

import re

from fetch      import get_json
from formatting import BLACK, GREY, YELLOW, ago, bold, color, line, site_tag, stat, timestamp


TAG      = site_tag('Hugging Face', BLACK, YELLOW)
RESERVED = ('blog', 'docs', 'learn', 'login', 'join', 'models', 'papers', 'posts', 'pricing', 'settings', 'tasks', 'organizations', 'enterprise', 'chat')


async def repository(session, match: re.Match) -> str | None:
	'''
	Parse a Hugging Face model, dataset, or space link using the public Hub API

	:param session: HTTP session
	:param match: Regex match with the repo type as group 1 (None for models) & repo id as group 2
	'''

	kind, repo_id = match.groups()

	if not kind and repo_id.split('/', 1)[0].lower() in RESERVED:
		return

	data  = await get_json(session, f'https://huggingface.co/api/{kind or "models"}/{repo_id}')
	label = {'datasets': 'dataset', 'spaces': 'space'}.get(kind, 'model')

	return line(TAG,
		bold(data['id']) + color(f' [{label}]', GREY),
		data.get('pipeline_tag') or data.get('sdk'),
		stat(data['downloads'], 'downloads') if 'downloads' in data else None,
		stat(data.get('likes', 0), 'likes'),
		(data.get('runtime') or {}).get('stage', '').lower() or None,
		color('gated', GREY) if data.get('gated') else None,
		color('updated ', GREY) + ago(timestamp(data['lastModified'])) if data.get('lastModified') else None
	)


ROUTES = (
	(re.compile(r'https?://(?:www\.)?huggingface\.co/(?:(datasets|spaces)/)?([\w.-]+/[\w.-]+)'), repository),
)
