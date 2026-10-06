"""Revoke only Ego's renewable session, record the real error, then reauthorize."""
from .chatgpt_oauth import Credentials, disconnect, http, TOKEN, RESOURCE, ChatGPTError, login
from u3.common import write, utc
from growthlab.records import ROOT


def main():
    destination = ROOT / 'evidence/d17/REVOCATION.json'
    if destination.exists():
        raise RuntimeError('revocation_probe_already_consumed')
    credentials = Credentials()
    with credentials.lock():
        store = credentials.read()
        account = store['accounts'][store['active']]
    revocation = disconnect(credentials)
    result = {'at_utc': utc(), 'scope': 'Only the app-owned Ego Companion renewable session',
              'revocation': revocation, 'live_error': None}
    if not revocation['remote_revocation_confirmed']:
        write(destination, result, exclusive=True)
        return
    try:
        # Do not retain the old secret on disk or in evidence.
        http(TOKEN, fields={'grant_type': 'refresh_token', 'client_id': account['client_id'],
                           'refresh_token': account['refresh_token'], 'resource': RESOURCE})
        result['unexpected_refresh_success'] = True
    except ChatGPTError as error:
        result['live_error'] = error.evidence()
    write(destination, result, exclusive=True)
    print('App session revoked; actual refresh rejection saved. Reopening official sign-in.', flush=True)
    login(credentials, account_id=account['client_id'])
    print('Ego session reauthorized; credentials remain DPAPI encrypted.', flush=True)


if __name__ == '__main__':
    main()
