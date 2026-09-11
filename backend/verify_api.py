import urllib.request, json

h = json.loads(urllib.request.urlopen('http://127.0.0.1:8000/api/health').read())
print('HEALTH:', h['status'], '| datasets:', h['active_datasets'])

for case_id in ['CASE_001_GENUINE', 'CASE_002_TAMPERED', 'CASE_003_UNCERTAIN']:
    req = urllib.request.Request(
        'http://127.0.0.1:8000/api/screenings/run',
        data=json.dumps({'sample_id': case_id, 'dataset': 'synthetic'}).encode(),
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    result = json.loads(urllib.request.urlopen(req).read())
    risk = result['risk_level']
    rs = result['risk_score']
    us = result['uncertainty_score']
    bio = result['biometric_result']
    nsig = len(result['evidence_signals'])
    ncon = len(result['conflicts'])
    print(f"{case_id}: risk={risk} | risk_score={rs:.2f} | uncertainty={us:.2f} | biometric={bio} | signals={nsig} | conflicts={ncon}")
