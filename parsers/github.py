#!/usr/bin/env python3
# IRC Link Bot - Developed by acidvegas in Python (https://github.com/acidvegas/irclinkbot)
# parsers/github.py

import re

from fetch      import get_json
from formatting import BLACK, CYAN, GREEN, GREY, LIGHTGREY, PURPLE, RED, YELLOW, ago, bold, clean, color, line, site_tag, stat, timestamp


TAG      = site_tag('GitHub', BLACK, LIGHTGREY)
API      = 'https://api.github.com'
RESERVED = ('about', 'apps', 'codespaces', 'collections', 'contact', 'customer-stories', 'dashboard', 'enterprise', 'events', 'explore', 'features', 'issues', 'login', 'marketplace', 'new', 'notifications', 'orgs', 'organizations', 'pricing', 'pulls', 'readme', 'search', 'security', 'settings', 'signup', 'site', 'sponsors', 'team', 'topics', 'trending')



async def commit(session, match: re.Match) -> str | None:
	'''
	Parse a GitHub commit link

	:param session: HTTP session
	:param match: Regex match with the owner, repo & sha as groups 1-3
	'''

	owner, repo, sha = match.groups()
	data             = await get_json(session, f'{API}/repos/{owner}/{repo}/commits/{sha}')
	stats            = data.get('stats', {})
	author           = (data.get('author') or {}).get('login') or data['commit']['author']['name']

	return line(TAG,
		color(f'{owner}/{repo}', GREY) + ' ' + bold(clean(data['commit']['message'].splitlines()[0], 200)),
		color(clean(author, 40), CYAN),
		color(f'+{stats.get("additions", 0)}', GREEN) + ' ' + color(f'-{stats.get("deletions", 0)}', RED),
		stat(len(data.get('files', [])), 'files'),
		ago(timestamp(data['commit']['author']['date']))
	)


async def gist(session, match: re.Match) -> str | None:
	'''
	Parse a GitHub gist link

	:param session: HTTP session
	:param match: Regex match with the gist id as group 1
	'''

	data  = await get_json(session, f'{API}/gists/{match.group(1)}')
	files = list(data.get('files', {}).values())

	return line(TAG,
		bold(clean(data.get('description') or files[0]['filename'], 200)),
		color((data.get('owner') or {}).get('login', 'anonymous'), CYAN),
		stat(len(files), 'files'),
		files[0].get('language') if files else None,
		stat(data.get('comments', 0), 'comments'),
		ago(timestamp(data['updated_at']))
	)


async def issue(session, match: re.Match) -> str | None:
	'''
	Parse a GitHub issue or pull request link

	:param session: HTTP session
	:param match: Regex match with the owner, repo & number as groups 1-3
	'''

	owner, repo, number = match.groups()
	data                = await get_json(session, f'{API}/repos/{owner}/{repo}/issues/{number}')
	kind                = 'PR' if 'pull_request' in data else 'Issue'

	if data.get('pull_request', {}).get('merged_at'):
		state = color('merged', PURPLE)
	elif data['state'] == 'open':
		state = color('open', GREEN)
	else:
		state = color('closed', RED)

	return line(TAG,
		color(f'{owner}/{repo} {kind} #{number}', GREY) + ' ' + bold(clean(data['title'], 200)),
		state,
		color(data['user']['login'], CYAN),
		stat(data.get('comments', 0), 'comments'),
		ago(timestamp(data['created_at']))
	)


async def repository(session, match: re.Match) -> str | None:
	'''
	Parse a GitHub repository link (also used for any deeper path within a repository)

	:param session: HTTP session
	:param match: Regex match with the owner & repo as groups 1-2
	'''

	owner, repo = match.groups()

	if owner.lower() in RESERVED:
		return

	data = await get_json(session, f'{API}/repos/{owner}/{repo.removesuffix(".git")}')

	return line(TAG,
		bold(data['full_name']),
		clean(data['description'], 150) if data.get('description') else None,
		color(data['language'], YELLOW) if data.get('language') else None,
		stat(data.get('stargazers_count', 0), 'stars'),
		stat(data.get('forks_count', 0), 'forks'),
		stat(data.get('open_issues_count', 0), 'issues'),
		(data.get('license') or {}).get('spdx_id') if (data.get('license') or {}).get('spdx_id') not in (None, 'NOASSERTION') else None,
		color('updated ', GREY) + ago(timestamp(data['pushed_at'])) if data.get('pushed_at') else None,
		color('archived', RED) if data.get('archived') else None
	)


async def user(session, match: re.Match) -> str | None:
	'''
	Parse a GitHub user or organization link

	:param session: HTTP session
	:param match: Regex match with the username as group 1
	'''

	if match.group(1).lower() in RESERVED:
		return

	data = await get_json(session, f'{API}/users/{match.group(1)}')
	name = color(clean(data['name'], 50), CYAN) + color(f' ({data["login"]})', GREY) if data.get('name') else color(data['login'], CYAN)

	return line(TAG,
		name + (color(' [org]', GREY) if data.get('type') == 'Organization' else ''),
		clean(data['bio'], 150) if data.get('bio') else None,
		stat(data.get('public_repos', 0), 'repos'),
		stat(data.get('followers', 0), 'followers'),
		color(data['location'], GREY) if data.get('location') else None
	)


ROUTES = (
	(re.compile(r'https?://gist\.github\.com/(?:[\w-]+/)?([0-9a-f]+)'),                        gist),
	(re.compile(r'https?://(?:www\.)?github\.com/([\w.-]+)/([\w.-]+)/(?:issues|pull)/(\d+)'), issue),
	(re.compile(r'https?://(?:www\.)?github\.com/([\w.-]+)/([\w.-]+)/commit/([0-9a-f]{7,40})'), commit),
	(re.compile(r'https?://(?:www\.)?github\.com/([\w.-]+)/([\w.-]+?)(?:[/?#].*)?$'),           repository),
	(re.compile(r'https?://(?:www\.)?github\.com/([\w-]+)/?(?:[?#].*)?$'),                      user),
)
