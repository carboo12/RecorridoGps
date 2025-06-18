import unittest
from backend.app import create_app, db
from backend.app.models import User, UserType, Site, Round, Access, Checkpoint, RoundCheckpoint

class BaseTestCase(unittest.TestCase):
    app = None  # Class variable to hold the app instance

    @classmethod
    def setUpClass(cls):
        if cls.app is None: # Create app only once per class
            cls.app = create_app()
            cls.app.config['TESTING'] = True
            cls.app.config['WTF_CSRF_ENABLED'] = False
            # Ensure SQLALCHEMY_DATABASE_URI is set for testing
            # cls.app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:*Admin2019#!@localhost:3306/rondasWeb_test' # Example for a test DB

        cls.client = cls.app.test_client()

        with cls.app.app_context():
            db.create_all()
            default_user_types = ['admin', 'dba', 'supervisor', 'guardas', 'user']
            for type_name in default_user_types:
                if not UserType.query.filter_by(name=type_name).first():
                    user_type = UserType(name=type_name, description=f"Default {type_name} role")
                    db.session.add(user_type)
            db.session.commit()

    @classmethod
    def tearDownClass(cls):
        with cls.app.app_context():
            # db.drop_all() # If using a dedicated test DB and want to clean it afterwards
            pass

    def setUp(self):
        self._clear_tables_before_test()

    def tearDown(self):
        self._clear_tables_after_test()

    def _clear_tables_before_test(self):
        with self.app.app_context():
            # More robust clearing of tables, respects FKs by order
            db.session.query(RoundCheckpoint).delete(synchronize_session=False)
            db.session.query(Round).delete(synchronize_session=False)
            db.session.query(Access).delete(synchronize_session=False)
            db.session.query(Checkpoint).delete(synchronize_session=False)
            db.session.query(User).delete(synchronize_session=False)
            db.session.query(Site).delete(synchronize_session=False)
            # UserType table is kept populated by setUpClass
            db.session.commit()

    def _clear_tables_after_test(self):
        # Can be same as before, or slightly different if needed
        # For now, ensure tables are clean for the next test
        self._clear_tables_before_test()


    def _get_token(self, username, password):
        response = self.client.post('/api/login', json={'username': username, 'password': password})
        if response.status_code == 200:
            return response.get_json().get('token')
        return None

    def _create_user_direct(self, username, password, role_name):
        from backend.app.routes import hash_password
        with self.app.app_context():
            user_type = UserType.query.filter_by(name=role_name).first()
            if not user_type: # Should have been created by setUpClass or previous direct calls
                # This might indicate an issue if types are expected to be strictly pre-defined
                # For robustness in tests, we can create it if missing, but it might hide setup issues.
                user_type = UserType(name=role_name, description=f"Test {role_name} role (created on-the-fly)")
                db.session.add(user_type)
                db.session.commit() # Commit immediately so User can use its ID

            user = User(username=username,
                        password_hash=hash_password(password),
                        user_type_id=user_type.id)
            db.session.add(user)
            db.session.commit()
            return user
