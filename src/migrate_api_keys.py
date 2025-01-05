from app_src.models import db, APIKey, User
from app import app


def migrate_api_keys():
    with app.app_context():
        # Get all existing API keys
        existing_keys = APIKey.query.all()

        # If there are any existing keys, associate them with the admin user
        if existing_keys:
            admin = User.query.filter_by(username="admin").first()
            if admin:
                for key in existing_keys:
                    key.user_id = admin.id
                db.session.commit()
                print("Existing API keys migrated to admin user")
            else:
                print("No admin user found")
        else:
            print("No existing API keys to migrate")

        # Add the new column
        with db.engine.connect() as conn:
            conn.execute(
                "ALTER TABLE api_keys ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id)"
            )
            conn.execute("ALTER TABLE api_keys ALTER COLUMN user_id SET NOT NULL")


if __name__ == "__main__":
    migrate_api_keys()
