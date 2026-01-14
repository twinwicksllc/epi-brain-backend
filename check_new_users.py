#!/usr/bin/env python3
"""
Check for new users in production database.
Run this script on the production server.
"""

from app.database import SessionLocal
from app.models.user import User
from datetime import datetime, timedelta

def check_new_users():
    db = SessionLocal()
    
    try:
        # Get total user count
        total_users = db.query(User).count()
        print(f'📊 Total users: {total_users}')
        
        # Get users created in the last 24 hours
        yesterday = datetime.utcnow() - timedelta(days=1)
        new_users_24h = db.query(User).filter(User.created_at >= yesterday).count()
        print(f'🆕 Users created in last 24 hours: {new_users_24h}')
        
        # Get users created in the last 7 days
        week_ago = datetime.utcnow() - timedelta(days=7)
        new_users_7days = db.query(User).filter(User.created_at >= week_ago).count()
        print(f'📈 Users created in last 7 days: {new_users_7days}')
        
        # Get users created in the last 30 days
        month_ago = datetime.utcnow() - timedelta(days=30)
        new_users_30days = db.query(User).filter(User.created_at >= month_ago).count()
        print(f'📆 Users created in last 30 days: {new_users_30days}')
        
        # Get breakdown by tier
        print('\n👥 Users by tier:')
        for tier in ['free', 'pro', 'enterprise']:
            tier_count = db.query(User).filter(User.tier == tier).count()
            print(f'  {tier.capitalize()}: {tier_count}')
        
        # Get most recent users
        print('\n🔥 Most recent users (last 5):')
        recent_users = db.query(User).order_by(User.created_at.desc()).limit(5).all()
        for i, user in enumerate(recent_users, 1):
            tier = user.tier.value if hasattr(user, 'tier') else 'unknown'
            email = user.email if user.email else 'No email'
            created = user.created_at.strftime('%Y-%m-%d %H:%M:%S')
            print(f'  {i}. {email}')
            print(f'     Tier: {tier} | Created: {created}')
        
        # Check if there are any new users in last 24h
        if new_users_24h > 0:
            print(f'\n✅ {new_users_24h} new user(s) in the last 24 hours!')
        else:
            print('\n⚠️  No new users in the last 24 hours')
        
        # Summary
        print('\n' + '='*50)
        print('SUMMARY')
        print('='*50)
        print(f'Total users: {total_users}')
        print(f'New this week: {new_users_7days}')
        print(f'New this month: {new_users_30days}')
        print(f'Growth rate (7 days): {new_users_7days} users')
        print('='*50)
        
    except Exception as e:
        print(f'❌ Error checking users: {e}')
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == '__main__':
    check_new_users()