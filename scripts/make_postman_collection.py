import json
from pathlib import Path

BASE = {'raw': '{{baseUrl}}', 'host': ['{{baseUrl}}']}

SAVE_TOKENS = (
    "const body = pm.response.json();",
    "if (body.tokens) {",
    "  pm.collectionVariables.set('accessToken', body.tokens.access);",
    "  pm.collectionVariables.set('refreshToken', body.tokens.refresh);",
    "}",
)

SAVE_CAMPAIGN = (
    "const body = pm.response.json();",
    "if (body.results && body.results.length) {",
    "  pm.collectionVariables.set('platform', body.results[0].platform);",
    "  pm.collectionVariables.set('campaignId', body.results[0].campaign_id);",
    "}",
)


def url(path, query=None):
    segments = [s for s in path.split('/') if s]
    entry = {
        'raw': '{{baseUrl}}/' + path + (('?' + '&'.join(f'{k}={v}' for k, v in query) if query else '')),
        'host': ['{{baseUrl}}'],
        'path': segments,
    }
    if query:
        entry['query'] = [{'key': k, 'value': v} for k, v in query]
    return entry


def request(name, method, path, body=None, query=None, script=None, auth=True):
    item = {
        'name': name,
        'request': {
            'method': method,
            'header': ([{'key': 'Content-Type', 'value': 'application/json'}] if body else []),
            'url': url(path, query),
        },
    }
    if body is not None:
        item['request']['body'] = {
            'mode': 'raw', 'raw': json.dumps(body, indent=2),
            'options': {'raw': {'language': 'json'}},
        }
    if not auth:
        item['request']['auth'] = {'type': 'noauth'}
    if script:
        item['event'] = [{'listen': 'test', 'script': {'type': 'text/javascript', 'exec': list(script)}}]
    return item


COLLECTION = {
    'info': {
        'name': 'CAT Dealer Snapshot API',
        'description': 'Backend for the CAT Dealer Snapshot dashboard. '
                       'Run "Dev token" first; the JWT is stored automatically.',
        'schema': 'https://schema.getpostman.com/json/collection/v2.1.0/collection.json',
    },
    'auth': {
        'type': 'bearer',
        'bearer': [{'key': 'token', 'value': '{{accessToken}}', 'type': 'string'}],
    },
    'variable': [
        {'key': 'baseUrl', 'value': 'http://127.0.0.1:8000/api'},
        {'key': 'accessToken', 'value': ''},
        {'key': 'refreshToken', 'value': ''},
        {'key': 'platform', 'value': 'google'},
        {'key': 'campaignId', 'value': ''},
        {'key': 'noteId', 'value': ''},
        {'key': 'flagId', 'value': ''},
    ],
    'item': [
        {
            'name': 'Auth',
            'item': [
                request('Dev token', 'POST', 'auth/dev-token/',
                        {'email': 'shiva@wppmedia.com', 'full_name': 'Shivam Sharma'},
                        script=SAVE_TOKENS, auth=False),
                request('Google login', 'POST', 'auth/google/',
                        {'credential': '<Google ID token from the React app>'},
                        script=SAVE_TOKENS, auth=False),
                request('Me', 'GET', 'auth/me/'),
                request('Refresh', 'POST', 'auth/refresh/', {'refresh': '{{refreshToken}}'},
                        auth=False),
                request('Logout', 'POST', 'auth/logout/', {'refresh': '{{refreshToken}}'}),
            ],
        },
        {
            'name': 'Reporting',
            'item': [
                request('Overview', 'GET', 'overview/', query=[('range', 'last_28_days')]),
                request('Overview - filtered', 'GET', 'overview/',
                        query=[('range', 'last_28_days'), ('market', 'DE'), ('platform', 'google,youtube')]),
                request('Overview - custom range', 'GET', 'overview/',
                        query=[('date_from', '2026-09-01'), ('date_to', '2026-09-30')]),
                request('Filters', 'GET', 'filters/'),
                request('Campaigns (cards / table)', 'GET', 'campaigns/',
                        query=[('range', 'last_28_days'), ('ordering', '-spend')],
                        script=SAVE_CAMPAIGN),
                request('Campaigns - off track only', 'GET', 'campaigns/',
                        query=[('status', 'off_track')]),
                request('Campaigns - search', 'GET', 'campaigns/',
                        query=[('search', 'Search'), ('market', 'UK')]),
                request('Campaigns - flagged only', 'GET', 'campaigns/', query=[('flagged', 'true')]),
                request('Campaign detail (modal)', 'GET', 'campaigns/{{platform}}/{{campaignId}}/'),
                request('Export CSV', 'GET', 'campaigns/export/', query=[('market', 'IT')]),
            ],
        },
        {
            'name': 'Notes',
            'item': [
                request('List notes', 'GET', 'campaigns/{{platform}}/{{campaignId}}/notes/'),
                request('Create note', 'POST', 'campaigns/{{platform}}/{{campaignId}}/notes/',
                        {'body': 'Checked with the dealer team, creative refresh planned.'},
                        script=("const b = pm.response.json();",
                                "if (b.id) pm.collectionVariables.set('noteId', b.id);")),
                request('Update note', 'PATCH',
                        'campaigns/{{platform}}/{{campaignId}}/notes/{{noteId}}/',
                        {'body': 'Updated note text.'}),
                request('Delete note', 'DELETE',
                        'campaigns/{{platform}}/{{campaignId}}/notes/{{noteId}}/'),
            ],
        },
        {
            'name': 'Flags',
            'item': [
                request('List flags', 'GET', 'campaigns/{{platform}}/{{campaignId}}/flags/',
                        query=[('status', 'open')]),
                request('Raise flag', 'POST', 'campaigns/{{platform}}/{{campaignId}}/flags/',
                        {'reason': 'performance', 'detail': 'CPL spiked in week 6.'},
                        script=("const b = pm.response.json();",
                                "if (b.id) pm.collectionVariables.set('flagId', b.id);")),
                request('Resolve flag', 'PATCH',
                        'campaigns/{{platform}}/{{campaignId}}/flags/{{flagId}}/',
                        {'status': 'resolved'}),
            ],
        },
        {
            'name': 'Targets',
            'item': [
                request('Get target', 'GET', 'campaigns/{{platform}}/{{campaignId}}/target/'),
                request('Set target', 'PUT', 'campaigns/{{platform}}/{{campaignId}}/target/',
                        {'kpi': 'cpl', 'target_value': '55.00', 'currency': 'EUR',
                         'direction': 'lower', 'at_risk_threshold_pct': '10.00',
                         'off_track_threshold_pct': '25.00'}),
            ],
        },
    ],
}

if __name__ == '__main__':
    out = Path(__file__).resolve().parents[1] / 'docs' / 'postman_collection.json'
    out.write_text(json.dumps(COLLECTION, indent=2), encoding='utf8')
    print(out)
