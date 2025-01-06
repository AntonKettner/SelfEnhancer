from app_src.models import db, APIKey, User
from flask import current_app


def migrate_api_keys():
    """Migrate API keys to include user_id column and associate with admin user."""
    with current_app.app_context():
        try:
            # Drop and recreate the api_keys table with the new schema
            print("Backing up existing API keys...")
            existing_keys = []
            try:
                # Try to get existing keys if table exists
                existing_keys = [(key.id, key.openai_key) for key in APIKey.query.all()]
            except Exception as e:
                print(f"Note: Could not fetch existing keys (this is normal for first run): {e}")

            print("Recreating api_keys table with new schema...")
            # Drop the table if it exists
            db.session.execute("DROP TABLE IF EXISTS api_keys")
            db.session.commit()

            # Create the table with the new schema
            db.create_all()
            db.session.commit()

            # Restore existing keys and associate with admin
            if existing_keys:
                print("Restoring existing API keys...")
                admin = User.query.filter_by(username="admin").first()
                if admin:
                    for key_id, openai_key in existing_keys:
                        new_key = APIKey(id=key_id, openai_key=openai_key, user_id=admin.id)
                        db.session.add(new_key)
                    db.session.commit()
                    print(f"Restored and migrated {len(existing_keys)} API keys to admin user")
                else:
                    print("No admin user found - skipping key restoration")
            else:
                print("No existing API keys to restore")

        except Exception as e:
            print(f"Error during migration: {e}")
            db.session.rollback()
            raise


if __name__ == "__main__":
    migrate_api_keys()
