#!/usr/bin/env python3
"""
QuickDesk Role Setup Script
This script helps you create admin and agent accounts for testing.
"""

import os
import sys
sys.path.append('.')

from app import app, db
from models import User
from werkzeug.security import generate_password_hash

def create_admin_user():
    """Create an admin user"""
    with app.app_context():
        # Check if admin already exists
        admin = User.query.filter_by(email='admin@quickdesk.com').first()
        if admin:
            print("Admin user already exists!")
            print(f"Email: admin@quickdesk.com")
            print(f"Current role: {admin.role}")
            return admin
        
        # Create new admin user
        admin = User(
            username='admin',
            email='admin@quickdesk.com',
            password_hash=generate_password_hash('admin123'),
            role='admin',
            first_name='Admin',
            last_name='User'
        )
        
        db.session.add(admin)
        db.session.commit()
        print("✓ Admin user created successfully!")
        print(f"Email: admin@quickdesk.com")
        print(f"Password: admin123")
        return admin

def create_agent_user():
    """Create an agent user"""
    with app.app_context():
        # Check if agent already exists
        agent = User.query.filter_by(email='agent@quickdesk.com').first()
        if agent:
            print("Agent user already exists!")
            print(f"Email: agent@quickdesk.com")
            print(f"Current role: {agent.role}")
            return agent
        
        # Create new agent user
        agent = User(
            username='agent',
            email='agent@quickdesk.com',
            password_hash=generate_password_hash('agent123'),
            role='agent',
            first_name='Support',
            last_name='Agent'
        )
        
        db.session.add(agent)
        db.session.commit()
        print("✓ Agent user created successfully!")
        print(f"Email: agent@quickdesk.com")
        print(f"Password: agent123")
        return agent

def promote_user_to_role(email, new_role):
    """Promote an existing user to a new role"""
    with app.app_context():
        user = User.query.filter_by(email=email).first()
        if not user:
            print(f"❌ User with email {email} not found!")
            return None
        
        old_role = user.role
        user.role = new_role
        db.session.commit()
        print(f"✓ User {email} promoted from {old_role} to {new_role}")
        return user

def list_all_users():
    """List all users and their roles"""
    with app.app_context():
        users = User.query.all()
        if not users:
            print("No users found in the database.")
            return
        
        print("\n=== All Users ===")
        for user in users:
            print(f"ID: {user.id} | Email: {user.email} | Role: {user.role} | Name: {user.first_name} {user.last_name}")

if __name__ == "__main__":
    print("QuickDesk Role Setup")
    print("===================")
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "create-admin":
            create_admin_user()
        elif command == "create-agent":
            create_agent_user()
        elif command == "create-both":
            create_admin_user()
            print()
            create_agent_user()
        elif command == "list-users":
            list_all_users()
        elif command == "promote" and len(sys.argv) == 4:
            email = sys.argv[2]
            role = sys.argv[3]
            if role in ['user', 'agent', 'admin']:
                promote_user_to_role(email, role)
            else:
                print("❌ Invalid role. Use: user, agent, or admin")
        else:
            print("❌ Invalid command or arguments")
            print("\nUsage:")
            print("  python setup_roles.py create-admin")
            print("  python setup_roles.py create-agent") 
            print("  python setup_roles.py create-both")
            print("  python setup_roles.py list-users")
            print("  python setup_roles.py promote <email> <role>")
    else:
        # Interactive mode
        print("\nWhat would you like to do?")
        print("1. Create admin user (admin@quickdesk.com)")
        print("2. Create agent user (agent@quickdesk.com)")
        print("3. Create both admin and agent")
        print("4. List all users")
        print("5. Promote existing user")
        
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice == "1":
            create_admin_user()
        elif choice == "2":
            create_agent_user()
        elif choice == "3":
            create_admin_user()
            print()
            create_agent_user()
        elif choice == "4":
            list_all_users()
        elif choice == "5":
            email = input("Enter user email: ").strip()
            role = input("Enter new role (user/agent/admin): ").strip()
            if role in ['user', 'agent', 'admin']:
                promote_user_to_role(email, role)
            else:
                print("❌ Invalid role. Use: user, agent, or admin")
        else:
            print("❌ Invalid choice")