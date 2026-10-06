import json
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from companion import chatgpt_oauth as oauth


class OAuthTests(unittest.TestCase):
    def test_callback_rejects_cross_attempt_duplicate_and_client_change(self):
        for query in ('state=wrong&code=c&client_id=issued',
                      'state=s&state=s&code=c&client_id=issued',
                      'state=s&code=c&client_id=other'):
            with self.assertRaises(oauth.ChatGPTError):
                oauth.callback_values(query, 's', 'issued')
        self.assertEqual(oauth.callback_values('state=s&code=c&client_id=issued', 's'), ('c', 'issued'))
        self.assertEqual(oauth.callback_values('state=s&code=c', 's', 'issued'), ('c', 'issued'))

    def test_consent_denied_and_dynamic_id_never_exchanged(self):
        for query in ('state=s&error=access_denied', 'state=s&code=c',
                      'state=s&code=c&client_id=dynamic_agent_client'):
            with self.assertRaises(oauth.ChatGPTError):
                oauth.callback_values(query, 's')

    def test_real_dpapi_storage_and_rotating_refresh(self):
        with tempfile.TemporaryDirectory() as directory:
            credentials = oauth.Credentials(Path(directory) / 'credentials.dpapi')
            initial = {'host_id': 'stable-host', 'active': 'issued', 'accounts': {'issued': {
                'client_id': 'issued', 'subject': 'synthetic', 'access_token': 'old-access-secret',
                'refresh_token': 'old-refresh-secret', 'expires_at': 0,
                'scopes': oauth.SCOPES.split()}}}
            credentials.write(initial)
            self.assertNotIn(b'old-refresh-secret', credentials.path.read_bytes())
            self.assertEqual(credentials.read(), initial)
            with patch.object(oauth, 'http', return_value={'access_token': 'new-access-secret',
                'refresh_token': 'new-refresh-secret', 'token_type': 'Bearer', 'expires_in': 3600}) as send:
                self.assertEqual(oauth.access_token(credentials), 'new-access-secret')
                self.assertEqual(send.call_args.kwargs['fields']['client_id'], 'issued')
                self.assertNotIn('scope', send.call_args.kwargs['fields'])
            self.assertEqual(credentials.read()['accounts']['issued']['refresh_token'], 'new-refresh-secret')
            self.assertNotIn(b'new-access-secret', credentials.path.read_bytes())
            self.assertEqual(credentials.read()['host_id'], 'stable-host')

    def test_terminal_refresh_clears_tokens_but_network_failure_preserves(self):
        with tempfile.TemporaryDirectory() as directory:
            credentials = oauth.Credentials(Path(directory) / 'credentials.dpapi')
            record = {'host_id': 'h', 'active': 'a', 'accounts': {'a': {'client_id': 'a',
                'subject': 's', 'access_token': 'secret', 'refresh_token': 'refresh',
                'expires_at': 0, 'scopes': oauth.SCOPES.split()}}}
            for code, preserved in [('chatgpt_connection_error', True), ('invalid_grant', False)]:
                credentials.write(record)
                with patch.object(oauth, 'http', side_effect=oauth.ChatGPTError(code)):
                    with self.assertRaises(oauth.ChatGPTError):
                        oauth.access_token(credentials)
                saved = credentials.read()['accounts']['a']
                self.assertEqual('refresh_token' in saved, preserved)
                self.assertEqual(saved['client_id'], 'a')

    def test_disconnect_revokes_and_retains_registration(self):
        with tempfile.TemporaryDirectory() as directory:
            credentials = oauth.Credentials(Path(directory) / 'credentials.dpapi')
            credentials.write({'host_id': 'h', 'active': 'a', 'accounts': {'a': {
                'client_id': 'a', 'subject': 's', 'refresh_token': 'secret', 'access_token': 'secret2'}}})
            with patch.object(oauth, 'discovery', return_value={'revocation_endpoint': oauth.AUTH + '/revoke'}), \
                 patch.object(oauth, 'http', return_value={}) as send:
                self.assertTrue(oauth.disconnect(credentials)['remote_revocation_confirmed'])
                self.assertEqual(send.call_args.kwargs['fields']['token_type_hint'], 'refresh_token')
            self.assertEqual(credentials.read()['accounts']['a'], {'client_id': 'a', 'subject': 's'})

    def test_identity_signature_nonce_expiry_and_audience(self):
        import jwt
        from cryptography.hazmat.primitives.asymmetric import rsa
        private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        claims = {'iss': oauth.AUTH, 'aud': 'issued', 'sub': 'synthetic', 'iat': time.time(),
                  'exp': time.time() + 60, 'nonce': 'nonce'}
        def encoded(changes):
            return jwt.encode({**claims, **changes}, private, algorithm='RS256')
        with patch.object(oauth, 'discovery', return_value={'jwks_uri': oauth.AUTH + '/jwks'}), \
             patch('jwt.PyJWKClient') as client:
            client.return_value.get_signing_key_from_jwt.return_value.key = private.public_key()
            self.assertEqual(oauth.validate_identity(encoded({}), 'issued', 'nonce')['sub'], 'synthetic')
            for changes in ({'aud': 'wrong'}, {'exp': 1}, {'nonce': 'wrong'}, {'iss': 'https://other.example'}):
                with self.assertRaises(oauth.ChatGPTError):
                    oauth.validate_identity(encoded(changes), 'issued', 'nonce')


if __name__ == '__main__':
    unittest.main()
