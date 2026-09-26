#!/usr/bin/env python3
# IRC Link Bot - Developed by acidvegas in Python (https://github.com/acidvegas/irclinkbot)
# linkbot.py

import asyncio
import collections
import json
import logging
import os
import re
import ssl
import time

from fetch   import create_session
from parsers import parse


SERVER   = 'irc.supernets.org'
PORT     = 6697
NICK     = 'LINK'
IDENT    = 'linkbot'
REALNAME = 'https://github.com/acidvegas/irclinkbot'
ADMIN    = 'acidvegas!~stillfree@most.dangerous.motherfuck'
INFO     = 'IRC Link Bot - Developed by acidvegas in Python - https://github.com/acidvegas/irclinkbot'

IGNORE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ignore.json')
ENV_FILE    = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env') # Holds NICKSERV_PASSWORD=...

JOIN_DELAY      = 6    # Seconds to wait after 001 before joining
KICK_DELAY      = 3    # Seconds to wait before rejoining after a kick
RETRY_DELAY     = 15   # Seconds between join attempts when we can not get in the channel
RECONNECT       = 15   # Seconds to wait before reconnecting
CONNECT_TIMEOUT = 15   # Seconds to wait for the TCP/TLS connection to the server
PING_TIMEOUT    = 300  # Seconds of silence from the server before we consider the connection dead
PARSE_TIMEOUT   = 20   # Max seconds to spend parsing a single link
INFO_COOLDOWN   = 10   # Per-channel cooldown for the @link command
RATE_LIMIT      = 5    # Max links parsed globally...
RATE_WINDOW     = 60   # ...per this many seconds (links over the limit are dropped)
CACHE_SIZE      = 1000 # Number of recent links to remember
CACHE_TTL       = 3600 # Seconds before a cached result is fetched again
REPEAT_WINDOW   = 600  # Seconds to stay silent when the same link is repeated in the same channel

JOIN_ERRORS = ('405', '437', '471', '473', '474', '475', '477', '489') # Too many channels, unavailable, full, invite only, banned, bad key, registered only, secure only

FORMATTING = re.compile(r'\x03\d{0,2}(?:,\d{1,2})?|[\x02\x0f\x11\x16\x1d\x1e\x1f]')
URL        = re.compile(r'https?://[^\s<>"\x00-\x1f\x7f]+', re.I)


def remember(store: collections.OrderedDict, key, value):
	'''
	Store a value in a bounded LRU dictionary, evicting the oldest entries past CACHE_SIZE

	:param store: Dictionary to store in
	:param key: Key
	:param value: Value
	'''

	store[key] = value
	store.move_to_end(key)

	while len(store) > CACHE_SIZE:
		store.popitem(last=False)


def load_env() -> dict:
	'''Load KEY=VALUE pairs from the .env file next to the script'''

	env = {}

	try:
		with open(ENV_FILE) as fp:
			for item in fp:
				if '=' in item and not item.lstrip().startswith('#'):
					key, value = item.split('=', 1)
					env[key.strip()] = value.strip().strip('\'"')
	except FileNotFoundError:
		pass

	return env


class Bot:
	'''IRC link title & metadata bot'''

	def __init__(self, channel: str):
		self.channel    = channel
		self.nickname   = NICK
		self.reader     = None
		self.writer     = None
		self.session    = None
		self.joined     = set()
		self.join_tasks = {}
		self.cooldowns  = {}
		self.tasks      = set() # Strong references so pending link tasks are not garbage collected
		self.rate       = collections.deque()       # Timestamps of recently parsed links
		self.cache      = collections.OrderedDict() # url -> (timestamp, result)
		self.posted     = collections.OrderedDict() # (channel, url) -> timestamp
		self.ignores    = self.load_ignores()
		self.password   = load_env().get('NICKSERV_PASSWORD')


	async def admin(self, nick: str, message: str):
		'''
		Handle a private message from the bot admin

		:param nick: Admin nickname
		:param message: Message text
		'''

		if message.startswith('.raw '):
			await self.raw(message[5:])

		elif (args := message.split()) and len(args) == 3 and args[0] == '@link' and args[1] == 'ignore' and args[2][:1] in '+-' and len(args[2]) > 1:
			target = args[2][1:].lower()

			if args[2][0] == '+':
				self.ignores.add(target)
				reply = f'Now ignoring {target}'
			else:
				self.ignores.discard(target)
				reply = f'No longer ignoring {target}'

			self.save_ignores()
			await self.raw(f'PRIVMSG {nick} :{reply}')


	async def connect(self):
		'''Connect to the server, register, and process lines until the connection drops'''

		self.reader, self.writer = await asyncio.wait_for(asyncio.open_connection(SERVER, PORT, ssl=ssl.create_default_context()), CONNECT_TIMEOUT)
		self.nickname            = NICK
		self.joined.clear()

		await self.raw(f'NICK {self.nickname}')
		await self.raw(f'USER {IDENT} 0 * :{REALNAME}')

		while True:
			data = await asyncio.wait_for(self.reader.readline(), PING_TIMEOUT)

			if not data:
				raise ConnectionError('connection closed by server')

			if line := data.decode('utf-8', 'replace').rstrip('\r\n'):
				logging.debug(f'>> {line}')
				await self.handle(line)


	async def handle(self, line: str):
		'''
		Handle a single line from the server

		:param line: Raw IRC line
		'''

		prefix = ''

		if line.startswith(':'):
			prefix, line = line[1:].split(' ', 1) if ' ' in line else (line[1:], '')

		if ' :' in line:
			line, trailing = line.split(' :', 1)
			params         = line.split() + [trailing]
		else:
			params = line.split()

		if not params:
			return

		command = params.pop(0).upper()
		nick    = prefix.split('!', 1)[0]

		if command == 'PING':
			await self.raw('PONG :' + (params[0] if params else ''))

		elif command == '001':
			logging.info(f'Connected to {SERVER}')
			self.nickname = params[0]
			if self.password:
				await self.raw(f'PRIVMSG NickServ :IDENTIFY {NICK} {self.password}')
			self.schedule_join(self.channel, JOIN_DELAY)

		elif command == '433': # Nickname in use
			self.nickname += '_'
			await self.raw(f'NICK {self.nickname}')

		elif command in JOIN_ERRORS and len(params) > 1 and params[1].lower() == self.channel.lower():
			logging.warning(f'Unable to join {self.channel} ({command}), retrying in {RETRY_DELAY} seconds')
			self.schedule_join(self.channel, RETRY_DELAY)

		elif command == 'NICK' and nick == self.nickname and params:
			self.nickname = params[0]

		elif command == 'JOIN' and nick == self.nickname and params:
			logging.info(f'Joined {params[0]}')
			self.joined.add(params[0].lower())

		elif command == 'PART' and nick == self.nickname and params:
			self.joined.discard(params[0].lower())

		elif command == 'KICK' and len(params) > 1 and params[1] == self.nickname:
			logging.warning(f'Kicked from {params[0]} by {nick}, rejoining in {KICK_DELAY} seconds')
			self.joined.discard(params[0].lower())
			self.schedule_join(params[0], KICK_DELAY)

		elif command == 'INVITE' and len(params) > 1 and params[1].lower() == self.channel.lower():
			logging.info(f'Invited to {params[1]} by {nick}')
			self.schedule_join(self.channel, 0)

		elif command == 'PRIVMSG' and len(params) > 1 and nick != self.nickname:
			await self.message(prefix, nick, params[0], params[1])


	def load_ignores(self) -> set:
		'''Load the ignore list from disk'''

		try:
			with open(IGNORE_FILE) as fp:
				return set(json.load(fp))
		except FileNotFoundError:
			return set()


	async def message(self, prefix: str, nick: str, target: str, message: str):
		'''
		Handle a PRIVMSG

		:param prefix: Sender hostmask
		:param nick: Sender nickname
		:param target: Channel or our nickname
		:param message: Message text
		'''

		if prefix == ADMIN and target == self.nickname:
			return await self.admin(nick, message)

		if not target.startswith(('#', '&')) or nick.lower() in self.ignores:
			return

		if message.startswith('\x01ACTION ') and message.endswith('\x01'):
			message = message[8:-1]
		elif message.startswith('\x01'):
			return

		if message.strip().lower() == '@link':
			if time.monotonic() - self.cooldowns.get(target.lower(), 0) >= INFO_COOLDOWN:
				self.cooldowns[target.lower()] = time.monotonic()
				await self.raw(f'PRIVMSG {target} :{INFO}')
			return

		if match := URL.search(FORMATTING.sub('', message)):
			url = match.group(0).rstrip('.,;:!?\'"*')

			while url.endswith(')') and url.count(')') > url.count('('):
				url = url[:-1]

			now = time.monotonic()
			key = (target.lower(), url)

			if now - self.posted.get(key, -REPEAT_WINDOW) < REPEAT_WINDOW:
				return

			while self.rate and now - self.rate[0] >= RATE_WINDOW:
				self.rate.popleft()

			if len(self.rate) >= RATE_LIMIT:
				return logging.warning(f'Rate limited, dropping {url}')

			self.rate.append(now)
			remember(self.posted, key, now)

			task = asyncio.create_task(self.title(target, url))
			self.tasks.add(task)
			task.add_done_callback(self.tasks.discard)


	async def raw(self, data: str):
		'''
		Send a raw line to the server

		:param data: Raw IRC line (without CRLF)
		'''

		logging.debug('<< ' + (data.replace(self.password, '********') if self.password else data))
		self.writer.write(data[:510].encode('utf-8', 'ignore') + b'\r\n')
		await self.writer.drain()


	async def run(self):
		'''Run the bot forever, reconnecting whenever the connection drops'''

		self.session = create_session()

		while True:
			try:
				await self.connect()
			except Exception as ex:
				logging.error(f'Disconnected: {ex.__class__.__name__}: {ex}')

			for task in self.join_tasks.values():
				task.cancel()

			self.join_tasks.clear()

			if self.writer:
				self.writer.close()

			logging.info(f'Reconnecting in {RECONNECT} seconds')
			await asyncio.sleep(RECONNECT)


	def save_ignores(self):
		'''Save the ignore list to disk'''

		with open(IGNORE_FILE, 'w') as fp:
			json.dump(sorted(self.ignores), fp, indent=4)


	def schedule_join(self, channel: str, delay: int):
		'''
		Join a channel after a delay, replacing any pending join for that channel

		:param channel: Channel to join
		:param delay: Seconds to wait before joining
		'''

		async def join():
			await asyncio.sleep(delay)
			if channel.lower() not in self.joined:
				await self.raw(f'JOIN {channel}')

		if task := self.join_tasks.get(channel.lower()):
			task.cancel()

		self.join_tasks[channel.lower()] = asyncio.create_task(join())


	async def title(self, target: str, url: str):
		'''
		Parse a link and send the result to the channel

		:param target: Channel to reply in
		:param url: URL to parse
		'''

		try:
			cached = self.cache.get(url)

			if cached and time.monotonic() - cached[0] < CACHE_TTL:
				result = cached[1]
			else:
				result = await asyncio.wait_for(parse(self.session, url), PARSE_TIMEOUT)
				remember(self.cache, url, (time.monotonic(), result))

			if result:
				await self.raw(f'PRIVMSG {target} :{result}')
		except Exception as ex:
			logging.warning(f'Failed to parse {url}: {ex.__class__.__name__}: {ex}')



if __name__ == '__main__':
	import argparse

	parser = argparse.ArgumentParser(description='IRC link title & metadata bot')
	parser.add_argument('-d', '--debug', action='store_true', help='join #dev instead of #superbowl & enable debug logging')
	args = parser.parse_args()

	logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO, format='%(asctime)s | %(levelname)8s | %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

	asyncio.run(Bot('#dev' if args.debug else '#superbowl').run())
