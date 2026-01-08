"""
Migration script to add voice_usage table
"""

from app.database import engine
from app.models.voice_usage import VoiceUsage


def create_voice_usage_table():
    """Create the voice_usage table if it doesn't exist"""
    try:
        VoiceUsage.__table__.create(engine, checkfirst=True)
        print("✅ Voice usage table created successfully")
        return True
    except Exception as e:
        print(f"❌ Error creating voice usage table: {e}")
        return False


if __name__ == "__main__":
    print("Creating voice_usage table...")
    create_voice_usage_table()