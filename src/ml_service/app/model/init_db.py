"""Database initialization script to create tables with proper schema."""
from .database import Base, engine


def init_db():
    """Create all database tables."""
    Base.metadata.create_all(bind=engine)
    print("✓ Database tables initialized")


def reset_db():
    """Drop all tables and recreate them - USE WITH CAUTION."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("✓ Database reset and reinitialized")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "reset":
        reset_db()
    else:
        init_db()
