from sqlalchemy import create_engine
from models import Base

DATABASE_URI = 'postgresql://postgres:SQLPassX&7@localhost/click_and_buy'
engine = create_engine(DATABASE_URI)

# Drop existing tables (if any)
Base.metadata.drop_all(engine)

# Create the tables with the updated schema
Base.metadata.create_all(engine)
