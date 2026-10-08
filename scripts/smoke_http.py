"""Exercise the running app over HTTP using local synthetic demo credentials."""
from http.cookiejar import CookieJar
import json
from pathlib import Path
import re
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, build_opener, HTTPCookieProcessor

BASE = 'http://127.0.0.1:8013'
credentials = json.loads((Path(__file__).resolve().parents[1] / '.demo-credentials.json').read_text())
opener = build_opener(HTTPCookieProcessor(CookieJar()))
page = opener.open(BASE + '/accounts/login/', timeout=10).read().decode()
csrf = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', page).group(1)
request = Request(BASE + '/accounts/login/', data=urlencode({
    'username': credentials['username'], 'password': credentials['password'],
    'csrfmiddlewaretoken': csrf,
}).encode(), headers={'Referer': BASE + '/accounts/login/'})
response = opener.open(request, timeout=10)
assert response.status == 200
assert 'Overview' in response.read().decode()
results = {'login_and_dashboard': 200}
for path in ['/certificates/', '/certificates/audit/']:
    response = opener.open(BASE + path, timeout=10)
    assert response.status == 200
    results[path] = response.status
try:
    opener.open(Request(BASE + '/', headers={'Host': 'untrusted.example'}), timeout=10)
    raise AssertionError('Untrusted Host was accepted')
except HTTPError as error:
    assert error.code == 400
    results['untrusted_host_rejected'] = error.code
response = opener.open('http://127.0.0.1:8014/', timeout=10)
assert json.loads(response.read())['status'] == 'ok'
results['fastapi_lab'] = response.status
print(json.dumps(results, indent=2))
