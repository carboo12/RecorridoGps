from functools import wraps
from flask import request, jsonify, current_app
import jwt
from .models import User # Assuming User model can be imported to verify user existence if needed

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']

        if not token:
            return jsonify({'message': 'Token is missing!'}), 401

        try:
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
            # Optionally, check if user from token still exists or is active
            # current_user = User.query.get(data['user_id'])
            # if not current_user:
            #     return jsonify({'message': 'Token user not found'}), 401

            # Store decoded token data in request context or pass to function
            # For simplicity, we'll often pass 'current_user_role' or 'current_user_id'
            # For now, let's assume data is implicitly available or passed if needed by specific role checks
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Token is invalid!'}), 401
        except Exception as e:
            return jsonify({'message': f'Token processing error: {str(e)}'}), 401

        # Pass decoded data to the decorated function
        return f(data, *args, **kwargs)
    return decorated

def roles_required(required_roles):
    def decorator(f):
        @wraps(f)
        @token_required # Ensures token is processed first
        def decorated_function(token_data, *args, **kwargs):
            user_role = token_data.get('role')
            if not user_role or user_role not in required_roles:
                return jsonify({'message': 'Unauthorized: Insufficient role permissions.'}), 403 # Forbidden

            # Pass token_data for further use if the decorated function needs it (e.g., user_id)
            return f(token_data, *args, **kwargs)
        return decorated_function
    return decorator

# Example specific role decorators (can be combined or made more granular)
def admin_roles_required(f):
    return roles_required(['admin', 'dba'])(f) # Admin and DBA have top privileges

def supervisor_or_admin_roles_required(f):
    return roles_required(['admin', 'dba', 'supervisor'])(f)
