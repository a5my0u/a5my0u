from pathlib import Path
import re
import yaml

def test_workflow_schedule_pins_permissions_and_dependencies():
    path=Path(__file__).parents[1]/'.github/workflows/update-profile.yml'
    value=yaml.load(path.read_text(),Loader=yaml.BaseLoader)
    assert value['on']['schedule'][0]['cron']=='0 23 * * *'
    assert 'workflow_dispatch' in value['on']
    assert value['permissions']=={'contents':'read'}
    assert value['concurrency']['cancel-in-progress']=='false'
    job=value['jobs']['update']
    assert job['permissions']=={'contents':'write'}
    for step in job['steps']:
        if 'uses' in step:assert re.fullmatch(r'actions/[a-z-]+@[0-9a-f]{40}',step['uses'])
    runs='\n'.join(s.get('run','') for s in job['steps'])
    assert 'scripts/update_profile.py' in runs and 'publish_generated.py --publish' in runs
    assert 'pull_request_target' not in value['on']
