from app_src.models import db, APIKey, User
from flask import current_app


def migrate_api_keys():
    """Migrate API keys to include user_id column and associate with admin user."""
    with current_app.app_context():
        try:
            # First add the column if it doesn't exist
            with db.engine.connect() as conn:
                try:
                    conn.execute(
                        "ALTER TABLE api_keys ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id)"
                    )
                    print("Added user_id column to api_keys table")
                except Exception as e:
                    print(f"Note: Column may already exist: {e}")

            # Get all existing API keys that don't have a user_id
            existing_keys = APIKey.query.filter(APIKey.user_id.is_(None)).all()

            if existing_keys:
                # Get or create admin user
                admin = User.query.filter_by(username="admin").first()
                if admin:
                    # Associate keys with admin user
                    for key in existing_keys:
                        key.user_id = admin.id
                    db.session.commit()
                    print(f"Migrated {len(existing_keys)} API keys to admin user")
                else:
                    print("No admin user found - skipping key migration")
            else:
                print("No API keys need migration")

            # Now make the column non-nullable
            with db.engine.connect() as conn:
                conn.execute("ALTER TABLE api_keys ALTER COLUMN user_id SET NOT NULL")
                print("Set user_id column to NOT NULL")

        except Exception as e:
            print(f"Error during migration: {e}")
            db.session.rollback()
            raise  # Re-raise the exception to be caught by the app's error handler


if __name__ == "__main__":
    migrate_api_keys()
