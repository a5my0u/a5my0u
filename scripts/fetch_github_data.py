"""Fetch a minimal, public-only snapshot. Runtime dependency: Python stdlib.

No private aggregate calendar or /user endpoint is used. Authentication only
raises API limits; it does not expand the defined public scope.
"""
from __future__ import annotations
import argparse
from collections import Counter
from datetime import date, datetime, timedelta, timezone
import json
import os
from pathlib import Path
import re
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler

API = 'https://api.github.com'

class DataError(RuntimeError):
    """Incomplete or unsafe data: preserve the previous published assets."""

class EmptyRepository(DataError):
    """GitHub explicitly confirmed that a repository has no Git history."""

class SameHostRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if urlsplit(newurl).scheme != 'https' or urlsplit(newurl).netloc != 'api.github.com':
            raise DataError('Refusing an API redirect outside api.github.com')
        return super().redirect_request(req, fp, code, msg, headers, newurl)

class GitHubClient:
    def __init__(self, token=None, timeout=20, retries=3, opener=None, sleep=time.sleep):
        self.token = token
        self.timeout = timeout
        self.retries = retries
        self.opener = opener or build_opener(SameHostRedirect())
        self.sleep = sleep

    def get(self, path, params=None):
        if not path.startswith('/') or path.startswith('//'):
            raise DataError('API paths must be relative to the fixed GitHub origin')
        url = API + path + (('?' + urlencode(params)) if params else '')
        headers = {'Accept': 'application/vnd.github+json', 'User-Agent': 'obsidian-emerald-profile', 'X-GitHub-Api-Version': '2026-03-10'}
        if self.token:
            headers['Authorization'] = 'Bearer ' + self.token
        for attempt in range(self.retries + 1):
            try:
                with self.opener.open(Request(url, headers=headers), timeout=self.timeout) as response:
                    if urlsplit(response.geturl()).netloc != 'api.github.com':
                        raise DataError('Unexpected response origin')
                    value = json.loads(response.read().decode('utf-8'))
                    return value, dict(response.headers)
            except HTTPError as exc:
                # Do not log response bodies, URLs containing identifiers, or credentials.
                if exc.code == 401:
                    raise DataError('GitHub authentication failed (401)') from None
                if exc.code == 409:
                    try:
                        message = json.loads(exc.read()).get('message')
                    except (ValueError, AttributeError):
                        message = None
                    if message == 'Git Repository is empty.':
                        raise EmptyRepository('Git repository is empty') from None
                limited = exc.code == 429 or (exc.code == 403 and (exc.headers.get('X-RateLimit-Remaining') == '0' or exc.headers.get('Retry-After')))
                retry = limited or exc.code in (500, 502, 503, 504)
                if not retry or attempt == self.retries:
                    raise DataError(f'GitHub request failed ({exc.code}); assets retained') from None
                delay = min(30, 2 ** attempt)
                retry_after = exc.headers.get('Retry-After')
                if retry_after:
                    try:
                        delay = float(retry_after)
                    except ValueError:
                        raise DataError('Unparseable GitHub rate-limit response') from None
                elif limited and exc.headers.get('X-RateLimit-Reset'):
                    delay = max(1, int(exc.headers['X-RateLimit-Reset']) - time.time() + 1)
                if delay > 30:
                    raise DataError('GitHub rate limit requires a later run; assets retained') from None
                self.sleep(delay)
            except (URLError, TimeoutError, OSError):
                if attempt == self.retries:
                    raise DataError('GitHub unavailable or timed out; assets retained') from None
                self.sleep(2 ** attempt)
            except (ValueError, UnicodeError):
                raise DataError('Invalid JSON from GitHub; assets retained') from None
        raise DataError('GitHub retry budget exhausted')

    def pages(self, path, params=None):
        params = dict(params or {})
        params['per_page'] = 100
        for page in range(1, 10001):
            params['page'] = page
            try:
                value, _ = self.get(path, params)
            except EmptyRepository:
                if page == 1 and path.endswith('/commits'):
                    return
                raise
            if not isinstance(value, list):
                raise DataError('Expected a paginated list')
            yield from value
            if len(value) < 100:
                return
        raise DataError('Pagination limit exceeded')

def integer(value, label):
    if type(value) is not int or value < 0:
        raise DataError(f'Missing or invalid {label}')
    return value

def repo_name(value):
    if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', value):
        raise DataError('Invalid repository identity')
    return value

def ensure_public(value):
    if not isinstance(value, dict) or value.get('private') is not False:
        raise DataError('Repository visibility is not explicitly public')
    if value.get('visibility', 'public') != 'public':
        raise DataError('Unexpected non-public repository')
    return value

def search_created(client, username, kind, start, end, excludes=()):
    """Paginate search; split by day range before the 1000-result search cap."""
    excluded = ' '.join('-repo:' + repo_name(n) for n in excludes)
    query = f'author:{username} is:{kind} is:public created:{start.isoformat()}..{end.isoformat()} {excluded}'.strip()
    payload, _ = client.get('/search/issues', {'q': query, 'per_page': 100, 'page': 1, 'sort': 'created', 'order': 'asc'})
    if not isinstance(payload, dict) or payload.get('incomplete_results') is not False:
        raise DataError('GitHub search results are incomplete')
    count = integer(payload.get('total_count'), 'search total')
    if count > 1000:
        if start == end:
            raise DataError('More than 1000 activities in one day; narrow the configured scope')
        mid = start + (end - start) // 2
        return search_created(client, username, kind, start, mid, excludes) + search_created(client, username, kind, mid + timedelta(days=1), end, excludes)
    items = payload.get('items')
    if not isinstance(items, list):
        raise DataError('Missing search items')
    for page in range(2, (count + 99) // 100 + 1):
        data, _ = client.get('/search/issues', {'q': query, 'per_page': 100, 'page': page, 'sort': 'created', 'order': 'asc'})
        if data.get('incomplete_results') is not False or data.get('total_count') != count or not isinstance(data.get('items'), list):
            raise DataError('Search changed while paginating; retry later')
        items.extend(data['items'])
    if len(items) != count or len({item.get('id') for item in items}) != count:
        raise DataError('Incomplete or duplicate search results')
    for item in items:
        if not isinstance(item.get('user'), dict) or item['user'].get('login', '').casefold() != username.casefold():
            raise DataError('Unexpected search author')
        if ('pull_request' in item) != (kind == 'pr'):
            raise DataError('Unexpected activity type')
    return items

def fetch_data(config, client=None, as_of=None):
    username = config['username']
    if not re.fullmatch(r'[A-Za-z0-9-]{1,39}', username):
        raise DataError('Invalid GitHub username')
    options = config['analytics']
    if options.get('public_only') is not True:
        raise DataError('Only public data is supported')
    if as_of is None:
        end = datetime.now(timezone.utc).date()
    elif isinstance(as_of, str):
        end = date.fromisoformat(as_of[:10])
    elif isinstance(as_of, datetime):
        end = as_of.date()
    else:
        end = as_of
    days = integer(options.get('days'), 'window days')
    if not 1 <= days <= 366:
        raise DataError('Window must be 1–366 days')
    start = end - timedelta(days=days - 1)
    client = client or GitHubClient(os.environ.get('GITHUB_TOKEN'), options.get('timeout_seconds', 20), options.get('max_retries', 3))
    excluded = {repo_name(n).casefold() for n in options.get('exclude_repositories', [])}
    excluded.add(config['repository'].casefold())
    repositories = []
    public_cache = {}
    for item in client.pages(f'/users/{username}/repos', {'type': 'owner', 'sort': 'full_name'}):
        ensure_public(item)
        full_name = repo_name(item.get('full_name'))
        if full_name.split('/')[0].casefold() != username.casefold():
            raise DataError('Unexpected repository owner')
        if type(item.get('fork')) is not bool or type(item.get('archived')) is not bool:
            raise DataError('Missing repository filtering metadata')
        if full_name.casefold() in excluded or (options.get('exclude_forks') and item['fork']) or (options.get('exclude_archived') and item['archived']):
            continue
        public_cache[full_name] = True
        repositories.append(item)
    daily = Counter()
    languages = Counter()
    commits = set()
    stars = 0
    repo_summaries = []
    for item in sorted(repositories, key=lambda r: r['full_name'].casefold()):
        full_name = item['full_name']
        stars += integer(item.get('stargazers_count'), 'stars')
        lang, _ = client.get('/repos/' + full_name + '/languages')
        if not isinstance(lang, dict):
            raise DataError('Missing language data')
        for name, size in lang.items():
            integer(size, 'language bytes')
            if name not in options.get('exclude_languages', []):
                languages[name] += size
        branch = item.get('default_branch')
        if not isinstance(branch, str) or not branch:
            raise DataError('Missing default branch')
        params = {'author': username, 'sha': branch, 'since': start.isoformat() + 'T00:00:00Z', 'until': end.isoformat() + 'T23:59:59Z'}
        # Empty Git repositories have no commits. Size is not a sufficient signal;
        # verify an empty repository via the dedicated 409 response in the API.
        for commit in client.pages('/repos/' + full_name + '/commits', params):
            sha = commit.get('sha')
            if not isinstance(sha, str) or not re.fullmatch('[a-f0-9]{40}', sha):
                raise DataError('Missing commit SHA')
            if not commit.get('author') or commit['author'].get('login', '').casefold() != username.casefold():
                raise DataError('Unexpected commit author')
            try:
                day = date.fromisoformat(commit['commit']['committer']['date'][:10])
            except (KeyError, TypeError, ValueError):
                raise DataError('Missing commit date') from None
            if start <= day <= end and sha not in commits:
                commits.add(sha)
                daily[day.isoformat()] += 1
        repo_summaries.append({'name': item['name'], 'full_name': full_name, 'url': 'https://github.com/' + full_name, 'stars': item['stargazers_count'], 'languages': dict(sorted(lang.items()))})
    activity_counts = {}
    for kind, key in [('pr', 'pull_requests'), ('issue', 'issues')]:
        activities = search_created(client, username, kind, start, end, sorted(excluded))
        for item in activities:
            url = urlsplit(item.get('repository_url', ''))
            if url.scheme != 'https' or url.netloc != 'api.github.com' or not url.path.startswith('/repos/'):
                raise DataError('Unexpected activity repository URL')
            full_name = repo_name(url.path.removeprefix('/repos/'))
            if full_name.casefold() in excluded:
                raise DataError('Search returned an excluded repository')
            if full_name not in public_cache:
                metadata, _ = client.get('/repos/' + full_name)
                ensure_public(metadata)
                public_cache[full_name] = True
            try:
                day = date.fromisoformat(item['created_at'][:10])
            except (KeyError, TypeError, ValueError):
                raise DataError('Missing activity date') from None
            if not start <= day <= end:
                raise DataError('Activity outside requested window')
            daily[day.isoformat()] += 1
        activity_counts[key] = len(activities)
    return {
        'schema_version': 1, 'username': username, 'as_of': end.isoformat(),
        'start_date': start.isoformat(), 'end_date': end.isoformat(),
        'scope': {'public_only': True, 'commits': 'Unique authored commits on default branches of owned public, non-fork, non-archived repositories; profile repository excluded. Grouped by Git committer date (UTC).', 'pull_requests': 'Public pull requests opened by this user during the window, excluding the profile repository.', 'issues': 'Public issues opened by this user during the window, excluding the profile repository.', 'stars': 'Current stars on included owned public repositories; lifetime stock, not a 365-day activity count.', 'calendar': 'Public commits + opened pull requests + opened issues under these scopes. Not the native GitHub contribution total.', 'languages': 'GitHub language byte counts on included owned public repositories. Not proficiency.', 'exclude_repositories': sorted(excluded), 'exclude_forks': bool(options.get('exclude_forks')), 'exclude_archived': bool(options.get('exclude_archived')), 'exclude_languages': sorted(options.get('exclude_languages', []))},
        'kpis': {'commits': len(commits), **activity_counts, 'stars': stars},
        'languages': dict(sorted(languages.items())),
        'contributions': [{'date': (start + timedelta(days=i)).isoformat(), 'count': daily[(start + timedelta(days=i)).isoformat()]} for i in range(days)],
        'repositories': repo_summaries,
        'source': {'api': 'GitHub REST API', 'version': '2026-03-10', 'fetched_date_utc': end.isoformat()}
    }

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--config', default='config/profile.json')
    p.add_argument('--output', required=True)
    p.add_argument('--as-of', help='UTC end date YYYY-MM-DD; defaults to today')
    args = p.parse_args()
    data = fetch_data(json.loads(Path(args.config).read_text(encoding='utf-8')), as_of=args.as_of)
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + '.tmp')
    temporary.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    temporary.replace(target)
    print('Public snapshot saved; no credentials or raw private fields included.')

if __name__ == '__main__':
    main()
