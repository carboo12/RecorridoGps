from flask import Flask, render_template, Blueprint
from .models import db, UserType # Import UserType
import os

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index_page():
    return render_template('index.html')

@main_bp.route('/login')
def login_page():
    return render_template('login.html')

@main_bp.route('/signup')
def signup_page():
    return render_template('signup.html')

@main_bp.route('/admin')
def admin_page():
    return render_template('admin.html')

@main_bp.route('/rounds')
def rounds_page():
    return render_template('rounds.html')

    @main_bp.route('/admin/users')
    # @login_required # If you have a Flask-Login style login_required, apply it
    def admin_users_page():
        # Further server-side role check can be added here if desired,
        # though API calls are already protected.
        # For example, using Flask-Login:
        # if not current_user.is_authenticated or current_user.user_type.name not in ['admin', 'dba']:
        #     return redirect(url_for('main.login_page')) # Or show an error
        return render_template('admin_users.html')


def populate_user_types(app_context_db):
    # Pre-populate UserTypes
    user_types_to_add = [
        {'name': 'admin', 'description': 'System Administrator with all privileges.'},
        {'name': 'dba', 'description': 'Database Administrator.'},
        {'name': 'supervisor', 'description': 'Supervisor role, can monitor and manage guards.'},
        {'name': 'guardas', 'description': 'Guard role, can perform rounds.'},
        {'name': 'user', 'description': 'Generic user role.'}
    ]
    for ut_data in user_types_to_add:
        user_type = UserType.query.filter_by(name=ut_data['name']).first()
        if not user_type:
            user_type = UserType(name=ut_data['name'], description=ut_data['description'])
            app_context_db.session.add(user_type)
    app_context_db.session.commit()

def create_app():
    app = Flask(__name__)

    app.config['SECRET_KEY'] = 'mysecretkey'

    # MySQL Configuration - CAUTION WITH PASSWORD
    db_user = "root"
    db_password = "*Admin2019#!" # THIS IS SENSITIVE
    db_host = "localhost"
    db_port = "3306"
    db_name = "rondasWeb"

    app.config['SQLALCHEMY_DATABASE_URI'] = \
        f'mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    from .routes import api_bp # Assuming routes.py exists
    app.register_blueprint(api_bp)

    app.register_blueprint(main_bp)

    with app.app_context():
        # Create all tables (if they don't exist)
        db.create_all()

        # Populate user types
        populate_user_types(db)

        # Remove the old database directory if it exists and is empty
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        sqlite_db_dir = os.path.join(project_root, 'database')
        sqlite_db_file = os.path.join(sqlite_db_dir, 'app.db')

        if os.path.exists(sqlite_db_file):
            try:
                os.remove(sqlite_db_file)
                print(f"Removed SQLite database file: {sqlite_db_file}")
                # Try to remove the directory if it's now empty
                if os.path.exists(sqlite_db_dir) and not os.listdir(sqlite_db_dir):
                    os.rmdir(sqlite_db_dir)
                    print(f"Removed empty SQLite database directory: {sqlite_db_dir}")
            except OSError as e:
                print(f"Error removing SQLite file/directory {sqlite_db_file} or {sqlite_db_dir}: {e}")
        elif os.path.exists(sqlite_db_dir) and not os.listdir(sqlite_db_dir):
            # If the file doesn't exist but the directory does and is empty
            try:
                os.rmdir(sqlite_db_dir)
                print(f"Removed empty SQLite database directory: {sqlite_db_dir}")
            except OSError as e:
                print(f"Error removing empty SQLite directory {sqlite_db_dir}: {e}")

    return app
