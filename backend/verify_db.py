import sys
import os

# Add the backend directory to sys.path to allow direct import of app
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app, db
from app.models import UserType

def verify():
    print("Starting verification...")
    try:
        app = create_app()
        print("create_app() called successfully.")

        with app.app_context():
            print("App context entered.")

            # Check UserType population
            user_type_count = UserType.query.count()
            print(f"Found {user_type_count} UserType entries in the database.")

            if user_type_count >= 5: # Should be 5 if all populated
                print("UserType table appears to be populated correctly.")

                # Optionally, list them
                # user_types = UserType.query.all()
                # for ut in user_types:
                #    print(f" - {ut.name}: {ut.description}")

            else:
                print(f"Error: UserType table population seems incorrect. Expected 5 entries, found {user_type_count}.")
                return False

            print("Verification successful: Database connected, tables created/checked, UserTypes populated.")
            return True

    except Exception as e:
        import traceback
        print(f"An error occurred during verification: {e}")
        print("Traceback:")
        print(traceback.format_exc())
        return False

if __name__ == '__main__':
    if verify():
        sys.exit(0) # Success
    else:
        sys.exit(1) # Failure
