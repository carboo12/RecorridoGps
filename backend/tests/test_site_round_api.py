from backend.tests.base import BaseTestCase
from backend.app.models import Site, db, User # Import User if not relying on BaseTestCase to create all users

class SiteRoundApiTestCase(BaseTestCase):
    def setUp(self):
        super().setUp() # Ensures tables are cleared and BaseTestCase.setUp users might be created if any.
                       # We will create specific users for this test class.
        self.admin_user = self._create_user_direct('testadmin_sra', 'adminpass', 'admin')
        self.supervisor_user = self._create_user_direct('testsupervisor_sra', 'superpass', 'supervisor')
        self.guard_user = self._create_user_direct('testguard_sra', 'guardpass', 'guardas')

        self.admin_token = self._get_token('testadmin_sra', 'adminpass')
        self.supervisor_token = self._get_token('testsupervisor_sra', 'superpass')
        self.guard_token = self._get_token('testguard_sra', 'guardpass')

        self.assertIsNotNone(self.admin_token, "Admin token setup failed in SiteRoundApiTestCase")
        self.assertIsNotNone(self.supervisor_token, "Supervisor token setup failed in SiteRoundApiTestCase")
        self.assertIsNotNone(self.guard_token, "Guard token setup failed in SiteRoundApiTestCase")

        with self.app.app_context():
            # Create a site for use in tests
            site = Site(name='Site Alpha SRA', coordinates='10,20', description='Initial test site')
            db.session.add(site)
            db.session.commit()
            self.site1_id = site.id # Store its ID for test methods

    def test_create_site_by_supervisor(self):
        response = self.client.post('/api/sites',
                                    headers={'x-access-token': self.supervisor_token},
                                    json={'name': 'Super Site SRA', 'coordinates': '30,40', 'description': 'Test site by supervisor'})
        self.assertEqual(response.status_code, 201, msg=response.get_data(as_text=True))
        data = response.get_json()
        self.assertIn('site_id', data)

    def test_create_site_by_guard_forbidden(self):
        response = self.client.post('/api/sites',
                                    headers={'x-access-token': self.guard_token},
                                    json={'name': 'Guard Site SRA Attempt', 'coordinates': '0,0'})
        self.assertEqual(response.status_code, 403, msg=response.get_data(as_text=True))

    def test_list_sites_by_any_authenticated_user(self):
        # Create another site to ensure listing works for multiple sites
        with self.app.app_context():
            site2 = Site(name='Site Beta SRA', coordinates='50,60')
            db.session.add(site2)
            db.session.commit()

        response = self.client.get('/api/sites', headers={'x-access-token': self.guard_token})
        self.assertEqual(response.status_code, 200, msg=response.get_data(as_text=True))
        data = response.get_json()
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 2, "Should be at least two sites listed")
        site_names = [s['name'] for s in data]
        self.assertIn('Site Alpha SRA', site_names)
        self.assertIn('Site Beta SRA', site_names)


    def test_get_specific_site_details(self):
        response = self.client.get(f'/api/sites/{self.site1_id}', headers={'x-access-token': self.guard_token})
        self.assertEqual(response.status_code, 200, msg=response.get_data(as_text=True))
        data = response.get_json()
        self.assertEqual(data['id'], self.site1_id)
        self.assertEqual(data['name'], 'Site Alpha SRA')
        self.assertEqual(data['coordinates'], '10,20')

    def test_start_round_by_guard(self):
        response = self.client.post('/api/rounds',
                                    headers={'x-access-token': self.guard_token},
                                    json={'site_id': self.site1_id})
        self.assertEqual(response.status_code, 201, msg=response.get_data(as_text=True))
        data = response.get_json()
        self.assertIn('round_id', data)
        # Additional check for user_id in response (though taken from token)
        with self.app.app_context():
            from backend.app.models import Round
            created_round = Round.query.get(data['round_id'])
            self.assertIsNotNone(created_round)
            self.assertEqual(created_round.user_id, self.guard_user.id)


    def test_list_own_rounds_by_guard(self):
        # Guard starts a round
        start_resp = self.client.post('/api/rounds', headers={'x-access-token': self.guard_token}, json={'site_id': self.site1_id})
        self.assertEqual(start_resp.status_code, 201, msg=start_resp.get_data(as_text=True))
        round_id_guard = start_resp.get_json()['round_id']

        # Admin starts a round (to ensure guard doesn't see it)
        admin_site = None
        with self.app.app_context(): # Ensure admin has a site to start a round on if needed
            admin_site = Site.query.filter_by(name="Admin Test Site for Rounds").first()
            if not admin_site:
                admin_site = Site(name="Admin Test Site for Rounds", coordinates="0,0")
                db.session.add(admin_site)
                db.session.commit()

        self.client.post('/api/rounds', headers={'x-access-token': self.admin_token}, json={'site_id': admin_site.id})

        # List rounds as guard
        list_resp = self.client.get('/api/rounds', headers={'x-access-token': self.guard_token})
        self.assertEqual(list_resp.status_code, 200, msg=list_resp.get_data(as_text=True))
        rounds_data = list_resp.get_json()
        self.assertEqual(len(rounds_data), 1, "Guard should only see their own round.")
        self.assertEqual(rounds_data[0]['id'], round_id_guard)
        self.assertEqual(rounds_data[0]['username'], self.guard_user.username)


    def test_list_all_rounds_by_admin(self):
        # Guard starts one round
        start_resp_guard = self.client.post('/api/rounds', headers={'x-access-token': self.guard_token}, json={'site_id': self.site1_id})
        self.assertEqual(start_resp_guard.status_code, 201)

        # Supervisor starts another round
        start_resp_super = self.client.post('/api/rounds', headers={'x-access-token': self.supervisor_token}, json={'site_id': self.site1_id})
        self.assertEqual(start_resp_super.status_code, 201)

        # List rounds as admin
        list_resp_admin = self.client.get('/api/rounds', headers={'x-access-token': self.admin_token})
        self.assertEqual(list_resp_admin.status_code, 200, msg=list_resp_admin.get_data(as_text=True))
        rounds_data_admin = list_resp_admin.get_json()
        # After table clearing, there should be exactly 2 rounds.
        self.assertEqual(len(rounds_data_admin), 2, "Admin should see rounds from guard and supervisor.")
        round_user_ids = {r['user_id'] for r in rounds_data_admin}
        self.assertIn(self.guard_user.id, round_user_ids)
        self.assertIn(self.supervisor_user.id, round_user_ids)


    def test_record_checkpoint_in_round_by_owner(self):
        # Guard starts a round
        start_round_resp = self.client.post('/api/rounds',
                                            headers={'x-access-token': self.guard_token},
                                            json={'site_id': self.site1_id})
        self.assertEqual(start_round_resp.status_code, 201)
        round_id = start_round_resp.get_json()['round_id']

        # Create a checkpoint for the site
        checkpoint_id = None
        with self.app.app_context():
            from backend.app.models import Checkpoint
            cp = Checkpoint(name="CP1", site_id=self.site1_id, description="First checkpoint")
            db.session.add(cp)
            db.session.commit()
            checkpoint_id = cp.id

        self.assertIsNotNone(checkpoint_id, "Checkpoint setup failed")

        # Record checkpoint
        record_cp_resp = self.client.post(f'/api/rounds/{round_id}/checkpoints',
                                          headers={'x-access-token': self.guard_token},
                                          json={'checkpoint_id': checkpoint_id, 'notes': 'All clear'})
        self.assertEqual(record_cp_resp.status_code, 201, msg=record_cp_resp.get_data(as_text=True))
        data = record_cp_resp.get_json()
        self.assertIn('round_checkpoint_id', data)

    def test_record_checkpoint_in_round_by_other_guard_forbidden(self):
        # Guard1 starts a round
        start_round_resp = self.client.post('/api/rounds',
                                            headers={'x-access-token': self.guard_token},
                                            json={'site_id': self.site1_id})
        self.assertEqual(start_round_resp.status_code, 201)
        round_id = start_round_resp.get_json()['round_id']

        # Create Guard2
        guard2_user = self._create_user_direct('testguard2_sra', 'guard2pass', 'guardas')
        guard2_token = self._get_token('testguard2_sra', 'guard2pass')
        self.assertIsNotNone(guard2_token)

        # Create a checkpoint
        checkpoint_id = None
        with self.app.app_context():
            from backend.app.models import Checkpoint
            cp = Checkpoint(name="CP2", site_id=self.site1_id)
            db.session.add(cp)
            db.session.commit()
            checkpoint_id = cp.id

        # Guard2 tries to record checkpoint in Guard1's round
        record_cp_resp = self.client.post(f'/api/rounds/{round_id}/checkpoints',
                                          headers={'x-access-token': guard2_token},
                                          json={'checkpoint_id': checkpoint_id})
        self.assertEqual(record_cp_resp.status_code, 403, msg=record_cp_resp.get_data(as_text=True))
