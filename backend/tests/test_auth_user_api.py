from backend.tests.base import BaseTestCase
# Models User, UserType are implicitly available via db from BaseTestCase context,
# or can be imported from backend.app.models if needed for type hinting or specific queries.

class AuthUserApiTestCase(BaseTestCase):

    def setUp(self):
        super().setUp()
        # Users created here will be cleaned up by BaseTestCase's setUp/tearDown logic
        self.admin_user = self._create_user_direct('testadmin_aua', 'adminpass', 'admin')
        self.guard_user = self._create_user_direct('testguard_aua', 'guardpass', 'guardas')

        self.admin_token = self._get_token('testadmin_aua', 'adminpass')
        self.guard_token = self._get_token('testguard_aua', 'guardpass')

        self.assertIsNotNone(self.admin_token, "Admin token setup failed in AuthUserApiTestCase.setUp")
        self.assertIsNotNone(self.guard_token, "Guard token setup failed in AuthUserApiTestCase.setUp")

    def test_user_login_success(self):
        # Re-login to ensure the mechanism is fine, even if token already fetched in setUp
        token = self._get_token('testadmin_aua', 'adminpass')
        self.assertIsNotNone(token)

    def test_user_login_nonexistent_user(self):
        response = self.client.post('/api/login', json={'username': 'nosuchuser_aua', 'password': 'fakepassword'})
        self.assertEqual(response.status_code, 401)
        json_response = response.get_json()
        self.assertIn('message', json_response)
        self.assertIn('User not found', json_response['message'])

    def test_user_login_wrong_password(self):
        response = self.client.post('/api/login', json={'username': 'testguard_aua', 'password': 'wrongpassword'})
        self.assertEqual(response.status_code, 401)
        json_response = response.get_json()
        self.assertIn('message', json_response)
        self.assertIn('Invalid credentials', json_response['message'])

    def test_create_user_by_admin(self):
        response = self.client.post('/api/users', headers={'x-access-token': self.admin_token},
                                    json={'username': 'newuser_aua', 'password': 'newpass', 'role': 'user'})
        self.assertEqual(response.status_code, 201, msg=f"API Response: {response.get_data(as_text=True)}")
        data = response.get_json()
        self.assertEqual(data['role'], 'user')

    def test_create_user_by_guard_forbidden(self):
        response = self.client.post('/api/users', headers={'x-access-token': self.guard_token},
                                    json={'username': 'newuserbyguard_aua', 'password': 'newpass', 'role': 'user'})
        self.assertEqual(response.status_code, 403, msg=f"API Response: {response.get_data(as_text=True)}")
        json_response = response.get_json()
        self.assertIn('message', json_response)
        self.assertIn('Insufficient role permissions', json_response['message'])

    def test_get_user_by_admin(self):
        response = self.client.get(f'/api/users/{self.guard_user.id}', headers={'x-access-token': self.admin_token})
        self.assertEqual(response.status_code, 200, msg=f"API Response: {response.get_data(as_text=True)}")
        self.assertEqual(response.get_json()['username'], 'testguard_aua')

    def test_get_user_by_self_or_other_auth_user(self):
        # Current policy allows any authenticated user to see any user's profile.
        response = self.client.get(f'/api/users/{self.admin_user.id}', headers={'x-access-token': self.guard_token})
        self.assertEqual(response.status_code, 200, msg=f"API Response: {response.get_data(as_text=True)}")
        self.assertEqual(response.get_json()['username'], 'testadmin_aua')

    def test_access_admin_route_no_token(self):
        # Example: creating user requires admin token (which is an admin route)
        response = self.client.post('/api/users',
                                    json={'username': 'nousertoken_aua', 'password': 'pass', 'role': 'user'})
        self.assertEqual(response.status_code, 401)
        json_response = response.get_json()
        self.assertIn('message', json_response)
        self.assertIn('Token is missing', json_response['message'])
