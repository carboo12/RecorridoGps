from flask import Blueprint, request, jsonify, current_app
from .models import db, User, Site, Checkpoint, Round, RoundCheckpoint, UserType # Add UserType
from datetime import datetime, timedelta
import hashlib
import jwt
from .auth_utils import token_required, roles_required, admin_roles_required, supervisor_or_admin_roles_required

api_bp = Blueprint('api', __name__, url_prefix='/api')

def hash_password(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

# User Management: Only Admin/DBA can create users or view specific user details (other than oneself)
@api_bp.route('/users', methods=['POST'])
@admin_roles_required
def create_user(token_data):
    data = request.get_json()
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({'message': 'Username and password are required'}), 400

    if User.query.filter_by(username=data['username']).first():
        return jsonify({'message': 'User already exists'}), 400

    role_name = data.get('role', 'guardas')
    user_type = UserType.query.filter_by(name=role_name).first()
    if not user_type:
        user_type = UserType.query.filter_by(name='user').first()
        if not user_type:
             return jsonify({'message': f"Invalid role: {role_name} and default 'user' type not found."}), 400

    hashed_password = hash_password(data['password'])
    new_user = User(username=data['username'], password_hash=hashed_password, user_type_id=user_type.id)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'User created successfully', 'user_id': new_user.id, 'role': user_type.name}), 201


@api_bp.route('/users/<int:user_id>', methods=['GET'])
@token_required
def get_user(token_data, user_id):
    # Future: could add logic: if token_data['user_id'] == user_id OR token_data['role'] in ['admin', 'dba']
    user = User.query.get_or_404(user_id)
    user_role_name = user.user_type.name if user.user_type else 'N/A'
    return jsonify({'id': user.id, 'username': user.username, 'role': user_role_name})

# Site Management: Supervisor, Admin, DBA can create/view sites
@api_bp.route('/sites', methods=['POST'])
@supervisor_or_admin_roles_required
def create_site(token_data):
    data = request.get_json()
    if not data or 'name' not in data: # Corrected key check
        return jsonify({'message': 'Site name is required'}), 400
    if Site.query.filter_by(name=data['name']).first():
        return jsonify({'message': 'Site already exists'}), 400
    new_site = Site(name=data['name'],
                    description=data.get('description'),
                    coordinates=data.get('coordinates'))
    db.session.add(new_site)
    db.session.commit()
    return jsonify({'message': 'Site created successfully', 'site_id': new_site.id}), 201


# List sites: any authenticated user can list sites
@api_bp.route('/sites', methods=['GET'])
@token_required
def get_sites(token_data):
    sites = Site.query.all()
    return jsonify([{
        'id': site.id,
        'name': site.name,
        'description': site.description,
        'coordinates': site.coordinates,
        'access_points': [{'id': ap.id, 'name': ap.name, 'coordinates': ap.coordinates, 'description': ap.description} for ap in site.access_points]
    } for site in sites])

@api_bp.route('/sites/<int:site_id>', methods=['GET'])
@token_required
def get_site(token_data, site_id):
    site = Site.query.get_or_404(site_id)
    access_points = [{'id': ap.id, 'name': ap.name, 'coordinates': ap.coordinates, 'description': ap.description} for ap in site.access_points]
    return jsonify({
        'id': site.id,
        'name': site.name,
        'description': site.description,
        'coordinates': site.coordinates,
        'access_points': access_points
    })

# Checkpoint Management: Supervisor, Admin, DBA
@api_bp.route('/sites/<int:site_id>/checkpoints', methods=['POST'])
@supervisor_or_admin_roles_required
def create_checkpoint(token_data, site_id):
    data = request.get_json()
    if not data or 'name' not in data: # Corrected key check
        return jsonify({'message': 'Checkpoint name is required'}), 400
    site = Site.query.get_or_404(site_id)
    new_checkpoint = Checkpoint(name=data['name'], description=data.get('description'), site_id=site.id)
    db.session.add(new_checkpoint)
    db.session.commit()
    return jsonify({'message': 'Checkpoint created successfully', 'checkpoint_id': new_checkpoint.id}), 201

@api_bp.route('/sites/<int:site_id>/checkpoints', methods=['GET'])
@token_required
def get_checkpoints(token_data, site_id):
    Site.query.get_or_404(site_id) # Ensure site exists
    checkpoints = Checkpoint.query.filter_by(site_id=site_id).all()
    return jsonify([{'id': cp.id, 'name': cp.name, 'description': cp.description, 'site_id': cp.site_id} for cp in checkpoints])

# Access Point Management: Supervisor, Admin, DBA
@api_bp.route('/sites/<int:site_id>/access_points', methods=['POST'])
@supervisor_or_admin_roles_required
def create_access_point(token_data, site_id):
    data = request.get_json()
    if not data or 'name' not in data or 'coordinates' not in data: # Corrected key check
        return jsonify({'message': 'Access point name and coordinates are required'}), 400
    site = Site.query.get_or_404(site_id)
    new_access_point = Access(name=data['name'], coordinates=data['coordinates'], site_id=site.id, description=data.get('description'))
    db.session.add(new_access_point)
    db.session.commit()
    return jsonify({'message': 'Access point created', 'access_point_id': new_access_point.id}), 201

@api_bp.route('/sites/<int:site_id>/access_points', methods=['GET'])
@token_required
def get_access_points(token_data, site_id):
    Site.query.get_or_404(site_id) # Ensure site exists
    access_points = Access.query.filter_by(site_id=site_id).all()
    return jsonify([{'id': ap.id, 'name': ap.name, 'coordinates': ap.coordinates, 'description': ap.description} for ap in access_points])


# Round Management
@api_bp.route('/rounds', methods=['POST'])
@token_required
def start_round(token_data):
    data = request.get_json()
    user_id_from_token = token_data.get('user_id')

    if not data or 'site_id' not in data: # Corrected key check
        return jsonify({'message': 'Site ID is required in request body'}), 400

    site_id_from_request = data['site_id']

    user = User.query.get_or_404(user_id_from_token)
    site = Site.query.get_or_404(site_id_from_request)

    active_round = Round.query.filter_by(user_id=user.id, status='active').first()
    if active_round:
        return jsonify({'message': f'User already has an active round (ID: {active_round.id})'}), 400

    new_round = Round(user_id=user.id, site_id=site.id)
    db.session.add(new_round)
    db.session.commit()
    return jsonify({'message': 'Round started successfully', 'round_id': new_round.id, 'start_time': new_round.start_time.isoformat()}), 201

@api_bp.route('/rounds/<int:round_id>/checkpoints', methods=['POST'])
@token_required
def record_round_checkpoint(token_data, round_id):
    data = request.get_json()
    if not data or 'checkpoint_id' not in data: # Corrected key check
        return jsonify({'message': 'Checkpoint ID is required'}), 400

    round_obj = Round.query.get_or_404(round_id)
    if round_obj.status != 'active':
        return jsonify({'message': 'Round is not active'}), 400

    user_id_from_token = token_data.get('user_id')
    user_role_from_token = token_data.get('role')
    if round_obj.user_id != user_id_from_token and user_role_from_token not in ['admin', 'dba', 'supervisor']:
        return jsonify({'message': 'Unauthorized: You cannot record checkpoints for this round.'}), 403

    checkpoint = Checkpoint.query.get_or_404(data['checkpoint_id'])
    if checkpoint.site_id != round_obj.site_id:
        return jsonify({'message': 'Checkpoint does not belong to the round site'}), 400

    new_round_checkpoint = RoundCheckpoint(
        round_id=round_obj.id,
        checkpoint_id=checkpoint.id,
        notes=data.get('notes')
    )
    db.session.add(new_round_checkpoint)
    db.session.commit()
    return jsonify({
        'message': 'Checkpoint recorded for round',
        'round_checkpoint_id': new_round_checkpoint.id,
        'timestamp': new_round_checkpoint.timestamp.isoformat()
    }), 201

@api_bp.route('/rounds/<int:round_id>/end', methods=['POST'])
@token_required
def end_round(token_data, round_id):
    round_obj = Round.query.get_or_404(round_id)
    if round_obj.status != 'active':
        return jsonify({'message': 'Round is not active or already ended'}), 400

    user_id_from_token = token_data.get('user_id')
    user_role_from_token = token_data.get('role')
    if round_obj.user_id != user_id_from_token and user_role_from_token not in ['admin', 'dba', 'supervisor']:
        return jsonify({'message': 'Unauthorized: You cannot end this round.'}), 403

    round_obj.end_time = datetime.utcnow()
    round_obj.status = 'completed'
    db.session.commit()
    return jsonify({'message': 'Round ended successfully', 'end_time': round_obj.end_time.isoformat()})

@api_bp.route('/rounds/<int:round_id>', methods=['GET'])
@token_required
def get_round_details(token_data, round_id):
    round_obj = Round.query.get_or_404(round_id)

    user_id_from_token = token_data.get('user_id')
    user_role_from_token = token_data.get('role')

    if round_obj.user_id != user_id_from_token and user_role_from_token not in ['admin', 'dba', 'supervisor']:
        return jsonify({'message': 'Unauthorized: You cannot view this round.'}), 403

    checkpoints_visited = RoundCheckpoint.query.filter_by(round_id=round_obj.id).order_by(RoundCheckpoint.timestamp).all()

    return jsonify({
        'id': round_obj.id,
        'user_id': round_obj.user_id,
        'username': round_obj.user.username,
        'site_id': round_obj.site_id,
        'site_name': round_obj.site.name,
        'start_time': round_obj.start_time.isoformat(),
        'end_time': round_obj.end_time.isoformat() if round_obj.end_time else None,
        'status': round_obj.status,
        'checkpoints_visited': [{
            'checkpoint_id': rcp.checkpoint_id,
            'checkpoint_name': rcp.checkpoint.name,
            'timestamp': rcp.timestamp.isoformat(),
            'notes': rcp.notes
        } for rcp in checkpoints_visited]
    })

@api_bp.route('/rounds', methods=['GET'])
@token_required
def list_rounds(token_data):
    user_id_from_token = token_data.get('user_id')
    user_role_from_token = token_data.get('role')

    query_user_id = request.args.get('user_id')

    rounds_query = Round.query.order_by(Round.start_time.desc())

    if user_role_from_token in ['admin', 'dba', 'supervisor']:
        if query_user_id:
            rounds_query = rounds_query.filter(Round.user_id == query_user_id)
    else:
        rounds_query = rounds_query.filter(Round.user_id == user_id_from_token)
        if query_user_id and int(query_user_id) != user_id_from_token :
             return jsonify({'message': 'Unauthorized: You can only view your own rounds.'}), 403

    rounds = rounds_query.all()
    return jsonify([{
        'id': r.id, 'user_id': r.user_id, 'username': r.user.username,
        'site_id': r.site_id, 'site_name': r.site.name,
        'start_time': r.start_time.isoformat(),
        'end_time': r.end_time.isoformat() if r.end_time else None,
        'status': r.status
    } for r in rounds])

@api_bp.route('/login', methods=['POST'])
def login_user():
    data = request.get_json()
    if not data or 'username' not in data or 'password' not in data: # Corrected 'in' check
        return jsonify({'message': 'Username and password are required'}), 400

    user = User.query.filter_by(username=data['username']).first()
    if not user:
        return jsonify({'message': 'User not found'}), 401

    if user.password_hash != hash_password(data['password']):
        return jsonify({'message': 'Invalid credentials'}), 401

    user_role_name = user.user_type.name if user.user_type else 'user'

    token_payload = {
        'user_id': user.id,
        'username': user.username,
        'role': user_role_name,
        'exp': datetime.utcnow() + timedelta(hours=24)
    }
    try:
        token = jwt.encode(token_payload, current_app.config['SECRET_KEY'], algorithm='HS256')
        return jsonify({'message': 'Login successful', 'token': token, 'user_id': user.id, 'role': user_role_name}), 200
    except Exception as e:
        return jsonify({'message': f'Error generating token: {str(e)}'}), 500
