import os
import logging
from flask import current_app
from flask_mail import Message
from app import mail

# Allowed file extensions for uploads
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'xls', 'xlsx'}

def allowed_file(filename):
    """Check if the uploaded file has an allowed extension"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_size(file_path):
    """Get file size in bytes"""
    try:
        return os.path.getsize(file_path)
    except OSError:
        return 0

def send_notification_email(ticket, notification_type, subject):
    """
    Send email notification for ticket events
    This is a mock implementation for the MVP - in production,
    you would implement actual email sending logic
    """
    try:
        # Mock email notification - log instead of sending
        recipients = []
        
        # Add ticket creator
        recipients.append(ticket.creator.email)
        
        # Add assigned agent if any
        if ticket.assignee:
            recipients.append(ticket.assignee.email)
        
        # Add admins for high priority tickets
        if ticket.priority in ['high', 'urgent']:
            from models import User
            admins = User.query.filter_by(role='admin', is_active=True).all()
            recipients.extend([admin.email for admin in admins])
        
        # Remove duplicates
        recipients = list(set(recipients))
        
        # Log the notification instead of sending actual email
        logging.info(f"Email notification: {notification_type}")
        logging.info(f"Subject: {subject}")
        logging.info(f"Recipients: {', '.join(recipients)}")
        logging.info(f"Ticket: #{ticket.id} - {ticket.subject}")
        
        # Uncomment below for actual email sending in production
        """
        if current_app.config.get('MAIL_USERNAME'):
            msg = Message(
                subject=f"[QuickDesk] {subject}",
                recipients=recipients,
                body=f"Ticket #{ticket.id}: {ticket.subject}\n\nStatus: {ticket.status.title()}\nPriority: {ticket.priority.title()}\n\nView ticket: {url_for('view_ticket', id=ticket.id, _external=True)}"
            )
            mail.send(msg)
        """
        
    except Exception as e:
        logging.error(f"Failed to send notification email: {str(e)}")

def format_file_size(size_bytes):
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"

def get_priority_color(priority):
    """Get Bootstrap color class for priority"""
    colors = {
        'low': 'secondary',
        'medium': 'info',
        'high': 'warning',
        'urgent': 'danger'
    }
    return colors.get(priority, 'info')

def get_status_color(status):
    """Get Bootstrap color class for status"""
    colors = {
        'open': 'primary',
        'in_progress': 'warning',
        'resolved': 'success',
        'closed': 'secondary'
    }
    return colors.get(status, 'secondary')

def truncate_text(text, max_length=100):
    """Truncate text to specified length with ellipsis"""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."

def get_user_role_display(role):
    """Get display name for user role"""
    role_names = {
        'user': 'End User',
        'agent': 'Support Agent',
        'admin': 'Administrator'
    }
    return role_names.get(role, role.title())
