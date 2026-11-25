"""Synthetic fixtures are confined to tests; no fixture is published."""
import copy
from datetime import date
import io
import json
from urllib.error import HTTPError, URLError
import pytest
from scripts.fetch_github_data import DataError, EmptyRepository, GitHubClient, SameHostRedirect, fetch_data, search_created

CONFIG = {'username':'fixture-user','repository':'fixture-user/profile','analytics':{'days':3,'public_only':True,'exclude_forks':True,'exclude_archived':True,'exclude_repositories':['fixture-user/profile'],'exclude_languages':[]}}

def repo(name='demo', **kwargs):
    return {'name':name,'full_name':'fixture-user/'+name,'private':False,'visibility':'public','fork':False,'archived':False,'default_branch':'main','stargazers_count':3,**kwargs}

class FakeClient:
    def __init__(self, repos=None, commits=None, languages=None, items=None):
        self.repos = repos if repos is not None else [repo(),repo('profile'),repo('fork',fork=True),repo('old',archived=True)]
        self.commits = commits if commits is not None else [{'sha':'a'*40,'author':{'login':'fixture-user'},'commit':{'committer':{'date':'2026-01-02T12:00:00Z'}}}]
        self.languages = languages if languages is not None else {'Python':90,'HTML':10}
        self.items = items or {}
        self.paths=[]
    def pages(self, path, params=None):
        self.paths.append(path)
        yield from (self.repos if path.startswith('/users/') else self.commits)
    def get(self, path, params=None):
        self.paths.append(path)
        if path.endswith('/languages'):
            return self.languages, {}
        if path == '/search/issues':
            kind = 'pr' if 'is:pr ' in params['q'] else 'issue'
            items = self.items.get(kind, [])
            return {'total_count':len(items),'incomplete_results':False,'items':items}, {}
        return repo(), {}

def test_scope_excludes_profile_forks_archives_and_counts_true_data():
    client=FakeClient()
    data=fetch_data(CONFIG, client, '2026-01-03')
    assert data['kpis']=={'commits':1,'pull_requests':0,'issues':0,'stars':3}
    assert data['languages']=={'HTML':10,'Python':90}
    assert [r['count'] for r in data['contributions']]==[0,1,0]
    assert data['start_date']=='2026-01-01'
    assert len(data['repositories'])==1
    assert all('/profile/' not in p and '/fork/' not in p for p in client.paths)
    assert 'email' not in json.dumps(data)

@pytest.mark.parametrize('bad', [None,-1,True,'2'])
def test_missing_or_bad_stars_fail_instead_of_zero(bad):
    with pytest.raises(DataError):
        fetch_data(CONFIG,FakeClient(repos=[repo(stargazers_count=bad)]),'2026-01-03')

def test_private_metadata_is_rejected_even_with_token_available():
    with pytest.raises(DataError,match='public'):
        fetch_data(CONFIG,FakeClient(repos=[repo(private=True)]),'2026-01-03')

def test_empty_valid_scope_is_zero_and_no_language_distribution():
    data=fetch_data(CONFIG,FakeClient(repos=[]),'2026-01-03')
    assert data['kpis']==dict.fromkeys(['commits','pull_requests','issues','stars'],0)
    assert data['languages']=={}
    assert len(data['contributions'])==3

def test_api_pagination_fetches_all_pages():
    c=GitHubClient()
    pages=[]
    def get(path, params):
        pages.append(params['page'])
        return ([{'id':i} for i in range(100)] if params['page']==1 else [{'id':100}]), {}
    c.get=get
    assert len(list(c.pages('/users/fixture-user/repos')))==101
    assert pages==[1,2]

def test_empty_repository_response_is_not_a_missing_value():
    c=GitHubClient()
    c.get=lambda *a, **k: (_ for _ in ()).throw(EmptyRepository('empty'))
    assert list(c.pages('/repos/fixture-user/empty/commits'))==[]
    with pytest.raises(EmptyRepository):
        list(c.pages('/users/fixture-user/repos'))

def activity(i, kind='issue', day='2026-01-02'):
    item={'id':i,'user':{'login':'fixture-user'},'repository_url':'https://api.github.com/repos/fixture-user/demo','created_at':day+'T10:00:00Z'}
    if kind=='pr': item['pull_request']={}
    return item

def test_public_search_activity_added_to_calendar():
    data=fetch_data(CONFIG,FakeClient(items={'pr':[activity(1,'pr')],'issue':[activity(2)]}),'2026-01-03')
    assert data['kpis']['pull_requests']==data['kpis']['issues']==1
    assert data['contributions'][1]['count']==3

@pytest.mark.parametrize('incomplete,count,items',[(True,0,[]),(False,2,[activity(1)]),(False,2,[activity(1),activity(1)])])
def test_search_incomplete_or_duplicate_fail(incomplete,count,items):
    class Client:
        def get(self,*a,**k): return {'incomplete_results':incomplete,'total_count':count,'items':items},{}
    with pytest.raises(DataError):
        search_created(Client(),'fixture-user','issue',date(2026,1,1),date(2026,1,3))

def test_search_splits_date_window_above_1000():
    calls=[]
    class Client:
        def get(self,path,params):
            calls.append(params['q'])
            if '2026-01-01..2026-01-02' in params['q']:
                return {'incomplete_results':False,'total_count':1001,'items':[]},{}
            items=[activity(1 if '01-01..' in params['q'] else 2)]
            return {'incomplete_results':False,'total_count':1,'items':items},{}
    assert len(search_created(Client(),'fixture-user','issue',date(2026,1,1),date(2026,1,2)))==2
    assert len(calls)==3

class Response(io.BytesIO):
    headers={}
    def geturl(self): return 'https://api.github.com/test'

def test_transient_failure_retries_then_succeeds():
    class Opener:
        count=0
        def open(self, req, timeout):
            self.count+=1
            if self.count==1: raise URLError('temporary')
            return Response(b'{"ok":true}')
    opener=Opener(); sleeps=[]
    data,_=GitHubClient(opener=opener,sleep=sleeps.append).get('/test')
    assert data['ok'] and opener.count==2 and sleeps==[1]

@pytest.mark.parametrize('code',[401,429,503])
def test_failed_http_never_contains_secret(code):
    class Opener:
        def open(self,*a,**k): raise HTTPError('https://api.github.com/test',code,'secret',{'Retry-After':'60'},io.BytesIO(b'token'))
    with pytest.raises(DataError) as exc:
        GitHubClient('SECRET',opener=Opener(),retries=0).get('/test')
    assert 'SECRET' not in str(exc.value) and 'token' not in str(exc.value)

def test_redirect_cannot_forward_authorization_outside_github():
    from urllib.request import Request
    with pytest.raises(DataError):
        SameHostRedirect().redirect_request(Request('https://api.github.com/test'),None,302,'',{},'https://evil.invalid/')
