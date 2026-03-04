from database import engine
import models

print("⚠️  WARNING: This will delete ALL tables and ALL data!")
confirm = input("Do you want to continue [y/N]: ")

if confirm.lower() in ["yes", "y"] :
    print("Dropping all tables...")
    models.Base.metadata.drop_all(bind=engine)
    print("✅ All tables dropped successfully!")
else:
    print("❌ Operation cancelled")