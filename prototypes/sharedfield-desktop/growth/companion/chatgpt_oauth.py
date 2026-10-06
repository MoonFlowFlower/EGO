"""Official SIWC public-client PKCE; app-owned, DPAPI-protected credentials.

No Codex credentials, client impersonation, API key or backend-api endpoint.
Only the local browser sees the authorization URL; it is never logged.
"""
import argparse
import base64
from contextlib import contextmanager
import hashlib
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
from pathlib import Path
import secrets
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
import webbrowser

from growthlab.records import ROOT
from .tokens import crypt

AUTH = 'https://auth.openai.com'
RESOURCE = 'https://api.openai.com/v1'
AUTHORIZE = AUTH + '/api/accounts/authorize'
TOKEN = AUTH + '/api/accounts/oauth/token'
SCOPES = 'openid profile email offline_access resource.invoke chatgpt.tokens.use.direct'
STORE = ROOT / 'runs/d17/credentials.dpapi'
TERMINAL_REFRESH = frozenset(('invalid_grant', 'invalid_refresh_token', 'token_expired',
    'refresh_token_expired', 'refresh_token_invalidated', 'refresh_token_reused'))


class ChatGPTError(RuntimeError):
    def __init__(self, code, *, status=None, body='', request_id=None, retry_after=None):
        super().__init__(code)
        self.code, self.status, self.body = str(code), status, body
        self.request_id, self.retry_after = request_id, retry_after

    def evidence(self):
        return {'code': self.code, 'http_status': self.status, 'body': self.body,
                'request_id': self.request_id, 'retry_after': self.retry_after}


def redact(text, values=()):
    for value in values:
        if isinstance(value, str) and value:
            text = text.replace(value, '[REDACTED]')
    return text


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def http(url, *, fields=None, bearer=None, payload=None, stream=False):
    headers = {'Accept': 'text/event-stream' if stream else 'application/json'}
    data = None
    sensitive = [bearer]
    if fields is not None:
        data = urllib.parse.urlencode(fields).encode()
        sensitive += [fields.get(k) for k in ('code', 'code_verifier', 'refresh_token', 'token')]
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False, separators=(',', ':')).encode()
        headers['Content-Type'] = 'application/json'
    if bearer:
        headers['Authorization'] = 'Bearer ' + bearer
    try:
        response = urllib.request.build_opener(NoRedirect).open(
            urllib.request.Request(url, data=data, headers=headers), timeout=60)
    except urllib.error.HTTPError as error:
        body = redact(error.read(1048576).decode('utf-8', errors='replace'), sensitive)
        try:
            obj = json.loads(body)
            e = obj.get('error', {})
            code = e.get('code') if isinstance(e, dict) else e
        except (ValueError, AttributeError):
            code = None
        raise ChatGPTError(code or 'chatgpt_http_' + str(error.code), status=error.code,
            body=body, request_id=error.headers.get('x-request-id'),
            retry_after=error.headers.get('Retry-After')) from None
    except (urllib.error.URLError, TimeoutError, OSError):
        raise ChatGPTError('chatgpt_connection_error') from None
    if stream:
        return response
    with response:
        raw = response.read(1048576)
    return json.loads(raw) if raw else {}


@contextmanager
def file_lock(path):
    """Same Windows byte lock as the existing single-model-call ledger."""
    import msvcrt
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a+b') as stream:
        if stream.tell() == 0:
            stream.write(b'0'); stream.flush()
        deadline = time.monotonic() + 180
        while True:
            stream.seek(0)
            try:
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
                break
            except OSError:
                if time.monotonic() >= deadline:
                    raise ChatGPTError('chatgpt_lock_timeout') from None
                time.sleep(.1)
        try:
            yield
        finally:
            stream.seek(0)
            msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)


class Credentials:
    def __init__(self, path=STORE):
        self.path = Path(path)

    def lock(self):
        return file_lock(self.path.with_suffix('.lock'))

    def read(self):
        if self.path.exists():
            return json.loads(crypt(self.path.read_bytes(), decrypt=True))
        return {'host_id': 'urn:uuid:' + str(uuid.uuid4()), 'accounts': {}, 'active': None}

    def write(self, value):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        encrypted = crypt(json.dumps(value, ensure_ascii=False).encode())
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(dir=self.path.parent, delete=False) as f:
                temporary = Path(f.name)
                f.write(encrypted); f.flush(); os.fsync(f.fileno())
            os.replace(temporary, self.path)
        finally:
            if temporary and temporary.exists():
                temporary.unlink()

    def status(self):
        with self.lock():
            store = self.read()
            active = store['accounts'].get(store['active'], {})
            return {'connected': bool(active.get('access_token')),
                    'plan_enabled': 'chatgpt.tokens.use.direct' in active.get('scopes', []),
                    'account': active.get('email'), 'expires_at': active.get('expires_at'),
                    'accounts': [{'id': k, 'email': v.get('email')} for k, v in store['accounts'].items()]}


def discovery():
    result = http(AUTH + '/.well-known/openid-configuration')
    if result.get('issuer') != AUTH:
        raise ChatGPTError('oidc_issuer_mismatch')
    for key in ('jwks_uri', 'revocation_endpoint'):
        parsed = urllib.parse.urlsplit(result[key])
        if parsed.scheme != 'https' or parsed.netloc != 'auth.openai.com':
            raise ChatGPTError('oidc_endpoint_mismatch')
    return result


def validate_identity(encoded, client_id, nonce):
    import jwt
    metadata = discovery()
    key = jwt.PyJWKClient(metadata['jwks_uri'], timeout=30).get_signing_key_from_jwt(encoded)
    try:
        identity = jwt.decode(encoded, key.key, algorithms=['RS256'], audience=client_id,
            issuer=AUTH, options={'require': ['exp', 'iat', 'iss', 'aud', 'sub', 'nonce']})
        if not secrets.compare_digest(identity['nonce'], nonce):
            raise ChatGPTError('oidc_nonce_mismatch')
    except jwt.PyJWTError:
        raise ChatGPTError('oidc_validation_failed') from None
    return identity


def save_tokens(old, tokens):
    if not tokens.get('access_token') or not tokens.get('refresh_token'):
        raise ChatGPTError('oauth_incomplete_token_set')
    if tokens.get('token_type', '').lower() != 'bearer':
        raise ChatGPTError('oauth_invalid_token_type')
    return {**old, **{k: tokens[k] for k in ('access_token', 'refresh_token', 'id_token') if k in tokens},
            'scopes': tokens['scope'].split() if 'scope' in tokens else old.get('scopes', []),
            'expires_at': time.time() + float(tokens['expires_in']),
            'earliest_refresh_at': tokens.get('earliest_refresh_at')}


def clear_tokens(account):
    return {k: v for k, v in account.items() if k not in
            ('access_token', 'refresh_token', 'id_token', 'expires_at', 'earliest_refresh_at', 'scopes')}


def callback_values(query, state, client_id=None):
    values = urllib.parse.parse_qs(query)
    if any(len(v) != 1 for v in values.values()) or not secrets.compare_digest(values.get('state', [''])[0], state):
        raise ChatGPTError('oauth_state_mismatch')
    if 'error' in values:
        raise ChatGPTError(values['error'][0])
    issued = values.get('client_id', [client_id])[0]
    if not issued or issued == 'dynamic_agent_client' or (client_id and issued != client_id):
        raise ChatGPTError('oauth_client_mismatch')
    if not values.get('code', [''])[0]:
        raise ChatGPTError('oauth_code_missing')
    return values['code'][0], issued


def login(credentials=None, *, account_id=None, timeout=900, launch=webbrowser.open):
    credentials = credentials or Credentials()
    with credentials.lock():
        store = credentials.read()
        credentials.write(store)  # Persist this host before first authorization.
        old = dict(store['accounts'].get(account_id, {}))
        if account_id and not old:
            raise ChatGPTError('unknown_account')
    state, nonce, verifier = (secrets.token_urlsafe(32) for _ in range(3))
    result = {}
    class Callback(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass  # Callback contains the authorization code; never access-log it.
        def do_GET(self):
            parsed = urllib.parse.urlsplit(self.path)
            if parsed.path != '/auth/callback':
                self.send_error(404); return
            try:
                result['grant'] = callback_values(parsed.query, state, old.get('client_id'))
                message = b'ChatGPT authorization received. You may return to Ego.'
                status = 200
            except ChatGPTError as error:
                if error.code == 'oauth_state_mismatch':
                    self.send_error(400); return
                result['error'] = error
                message, status = b'Authorization failed. Return to Ego.', 400
            self.send_response(status)
            self.send_header('Content-Type', 'text/plain; charset=utf-8')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Content-Length', str(len(message)))
            self.end_headers(); self.wfile.write(message)
    with HTTPServer(('127.0.0.1', 0), Callback) as server:
        server.timeout = .5
        redirect = f'http://127.0.0.1:{server.server_port}/auth/callback'
        parameters = {'client_id': old.get('client_id', 'dynamic_agent_client'),
            'ext_agent_host_id': store['host_id'], 'response_type': 'code', 'redirect_uri': redirect,
            'scope': SCOPES, 'resource': RESOURCE, 'state': state, 'nonce': nonce,
            'code_challenge_method': 'S256',
            'code_challenge': base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip('=')}
        if old:
            if old.get('id_token'):
                parameters['id_token_hint'] = old['id_token']
        else:
            parameters['agent_name_hint'] = 'Ego Companion'
        if not launch(AUTHORIZE + '?' + urllib.parse.urlencode(parameters)):
            raise ChatGPTError('system_browser_unavailable')
        print('Continue with ChatGPT opened in your browser; waiting for the local callback.', flush=True)
        deadline = time.monotonic() + timeout
        while not result and time.monotonic() < deadline:
            server.handle_request()
    if not result:
        raise ChatGPTError('oauth_callback_timeout')
    if 'error' in result:
        raise result['error']
    code, issued = result['grant']
    tokens = http(TOKEN, fields={'grant_type': 'authorization_code', 'client_id': issued,
        'code': code, 'code_verifier': verifier, 'redirect_uri': redirect, 'resource': RESOURCE})
    identity = validate_identity(tokens['id_token'], issued, nonce)
    if old and identity['sub'] != old['subject']:
        raise ChatGPTError('oauth_account_mismatch')
    record = save_tokens({'client_id': issued, 'subject': identity['sub'], 'email': identity.get('email')}, tokens)
    with credentials.lock():
        store = credentials.read()
        store['accounts'][issued] = record
        store['active'] = issued
        credentials.write(store)
    return credentials.status()


def access_token(credentials=None):
    credentials = credentials or Credentials()
    with credentials.lock():
        store = credentials.read()
        account = store['accounts'].get(store['active'], {})
        if not account.get('access_token'):
            raise ChatGPTError('chatgpt_login_required')
        if 'chatgpt.tokens.use.direct' not in account.get('scopes', []):
            raise ChatGPTError('chatgpt_plan_permission_required')
        if account['expires_at'] <= time.time() + 60:
            try:
                tokens = http(TOKEN, fields={'grant_type': 'refresh_token', 'client_id': account['client_id'],
                    'refresh_token': account['refresh_token'], 'resource': RESOURCE})
            except ChatGPTError as error:
                if error.code in TERMINAL_REFRESH:
                    store['accounts'][store['active']] = clear_tokens(account)
                    credentials.write(store)
                raise
            account = save_tokens(account, tokens)
            store['accounts'][store['active']] = account
            credentials.write(store)
            if 'chatgpt.tokens.use.direct' not in account['scopes']:
                raise ChatGPTError('chatgpt_plan_permission_required')
        return account['access_token']


def disconnect(credentials=None):
    credentials = credentials or Credentials()
    confirmed, error_evidence = False, None
    with credentials.lock():
        store = credentials.read()
        account = store['accounts'].get(store['active'], {})
        try:
            if account.get('refresh_token'):
                http(discovery()['revocation_endpoint'], fields={'token': account['refresh_token'],
                    'token_type_hint': 'refresh_token', 'client_id': account['client_id']})
                confirmed = True
        except ChatGPTError as error:
            error_evidence = error.evidence()
        finally:
            if store['active'] in store['accounts']:
                store['accounts'][store['active']] = clear_tokens(account)
                credentials.write(store)
    return {'disconnected_locally': True, 'remote_revocation_confirmed': confirmed, 'error': error_evidence}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('operation', choices=('login', 'status', 'disconnect'))
    parser.add_argument('--account')
    args = parser.parse_args()
    try:
        result = login(account_id=args.account) if args.operation == 'login' else (
            disconnect() if args.operation == 'disconnect' else Credentials().status())
        # Account identities stay local; evidence exports must not copy them.
        print(json.dumps(result, ensure_ascii=False))
    except ChatGPTError as error:
        print(json.dumps({'error': error.evidence()}, ensure_ascii=False))
        raise SystemExit(1)


if __name__ == '__main__':
    main()
