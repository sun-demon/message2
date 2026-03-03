from database import engine
from models import User, Chat, Message
import models

print("Creating database tables...")
models.Base.metadata.create_all(bind=engine)
print("✅ Tables created successfully!")
