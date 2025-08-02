from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from app import db

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')  # user, agent, admin
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tickets = db.relationship('Ticket', foreign_keys='Ticket.user_id', backref='creator', lazy='dynamic')
    assigned_tickets = db.relationship('Ticket', foreign_keys='Ticket.assigned_to', backref='assignee', lazy='dynamic')
    comments = db.relationship('TicketComment', backref='author', lazy='dynamic')
    votes = db.relationship('TicketVote', backref='user', lazy='dynamic')
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def can_edit_ticket(self, ticket):
        """Check if user can edit a ticket"""
        if self.role == 'admin':
            return True
        if self.role == 'agent':
            return True
        if self.role == 'user' and ticket.user_id == self.id:
            return True
        return False
    
    def can_assign_tickets(self):
        """Check if user can assign tickets"""
        return self.role in ['admin', 'agent']

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    tickets = db.relationship('Ticket', backref='category', lazy='dynamic')
    
    def __repr__(self):
        return f'<Category {self.name}>'

class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='open')  # open, in_progress, resolved, closed
    priority = db.Column(db.String(10), default='medium')  # low, medium, high, urgent
    
    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    assigned_to = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = db.Column(db.DateTime, nullable=True)
    closed_at = db.Column(db.DateTime, nullable=True)
    
    # Vote tracking
    upvotes = db.Column(db.Integer, default=0)
    downvotes = db.Column(db.Integer, default=0)
    
    # Relationships
    comments = db.relationship('TicketComment', backref='ticket', lazy='dynamic', cascade='all, delete-orphan')
    attachments = db.relationship('TicketAttachment', backref='ticket', lazy='dynamic', cascade='all, delete-orphan')
    votes = db.relationship('TicketVote', backref='ticket', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Ticket {self.id}: {self.subject}>'
    
    @property
    def status_badge_class(self):
        """Return Bootstrap badge class for status"""
        status_classes = {
            'open': 'bg-primary',
            'in_progress': 'bg-warning text-dark',
            'resolved': 'bg-success',
            'closed': 'bg-secondary'
        }
        return status_classes.get(self.status, 'bg-secondary')
    
    @property
    def priority_badge_class(self):
        """Return Bootstrap badge class for priority"""
        priority_classes = {
            'low': 'bg-light text-dark',
            'medium': 'bg-info',
            'high': 'bg-warning text-dark',
            'urgent': 'bg-danger'
        }
        return priority_classes.get(self.priority, 'bg-info')
    
    def get_user_vote(self, user_id):
        """Get user's vote for this ticket"""
        return TicketVote.query.filter_by(ticket_id=self.id, user_id=user_id).first()

class TicketComment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    is_internal = db.Column(db.Boolean, default=False)  # Internal comments visible only to agents/admin
    
    # Foreign keys
    ticket_id = db.Column(db.Integer, db.ForeignKey('ticket.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<TicketComment {self.id} for Ticket {self.ticket_id}>'

class TicketAttachment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200), nullable=False)
    original_filename = db.Column(db.String(200), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)
    mime_type = db.Column(db.String(100), nullable=False)
    
    # Foreign keys
    ticket_id = db.Column(db.Integer, db.ForeignKey('ticket.id'), nullable=False)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    uploader = db.relationship('User', backref='uploaded_files')
    
    def __repr__(self):
        return f'<TicketAttachment {self.original_filename}>'

class TicketVote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vote_type = db.Column(db.String(10), nullable=False)  # 'up' or 'down'
    
    # Foreign keys
    ticket_id = db.Column(db.Integer, db.ForeignKey('ticket.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Unique constraint to prevent duplicate votes
    __table_args__ = (db.UniqueConstraint('ticket_id', 'user_id', name='unique_ticket_user_vote'),)
    
    def __repr__(self):
        return f'<TicketVote {self.vote_type} by User {self.user_id} for Ticket {self.ticket_id}>'
