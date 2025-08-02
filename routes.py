import os
import uuid
from datetime import datetime
from flask import render_template, redirect, url_for, flash, request, abort, send_from_directory, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from sqlalchemy import or_, desc, asc, func
from sqlalchemy.orm import joinedload

from app import app, db
from models import User, Ticket, Category, TicketComment, TicketAttachment, TicketVote
from forms import (LoginForm, RegisterForm, TicketForm, TicketUpdateForm, CommentForm, 
                  CategoryForm, UserEditForm, SearchForm, VoteForm)
from utils import send_notification_email, allowed_file, get_file_size

# Template helper functions
@app.template_global()
def get_ticket_count():
    """Get ticket count for current user"""
    if current_user.is_authenticated:
        if current_user.role == 'user':
            return Ticket.query.filter_by(user_id=current_user.id, status='open').count()
        else:
            return Ticket.query.filter_by(status='open').count()
    return 0

@app.template_filter('format_datetime')
def format_datetime(dt):
    """Format datetime for display"""
    if dt:
        return dt.strftime('%Y-%m-%d %H:%M')
    return ''

@app.template_global()
def get_current_login_role():
    """Get the current login role from session"""
    return session.get('login_as_role', current_user.role if current_user.is_authenticated else 'user')

@app.template_global()
def can_access_admin():
    """Check if current user can access admin features"""
    if not current_user.is_authenticated:
        return False
    login_role = get_current_login_role()
    return login_role == 'admin' and current_user.role in ['admin']

@app.template_global()
def can_access_agent():
    """Check if current user can access agent features"""
    if not current_user.is_authenticated:
        return False
    login_role = get_current_login_role()
    return login_role in ['admin', 'agent'] and current_user.role in ['admin', 'agent']

# Authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        # Allow login with username or email
        user = User.query.filter(
            or_(User.username == form.username.data, User.email == form.username.data)
        ).first()
        
        if user and check_password_hash(user.password_hash, form.password.data):
            if user.is_active:
                # Check if user has the required role permissions
                selected_role = form.role.data
                user_role = user.role
                
                # Role hierarchy check: admin can access any role, agent can access agent/user, user can only access user
                role_hierarchy = {'admin': 3, 'agent': 2, 'user': 1}
                
                if role_hierarchy.get(user_role, 0) >= role_hierarchy.get(selected_role, 0):
                    login_user(user, remember=form.remember_me.data)
                    
                    # Store the selected role in session for UI purposes
                    session['login_as_role'] = selected_role
                    
                    next_page = request.args.get('next')
                    role_name = {'admin': 'Administrator', 'agent': 'Support Agent', 'user': 'End User'}[selected_role]
                    flash(f'Welcome back, {user.full_name}! Logged in as {role_name}.', 'success')
                    return redirect(next_page) if next_page else redirect(url_for('dashboard'))
                else:
                    flash(f'You do not have {form.role.data} permissions. Your role is: {user.role}', 'error')
            else:
                flash('Your account has been deactivated. Please contact an administrator.', 'error')
        else:
            flash('Invalid username/email or password.', 'error')
    
    return render_template('auth/login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = RegisterForm()
    if form.validate_on_submit():
        # Check if username or email already exists
        if User.query.filter_by(username=form.username.data).first():
            flash('Username already exists.', 'error')
            return render_template('auth/register.html', form=form)
        
        if User.query.filter_by(email=form.email.data).first():
            flash('Email already registered.', 'error')
            return render_template('auth/register.html', form=form)
        
        # Create new user
        user = User(
            username=form.username.data,
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            password_hash=generate_password_hash(form.password.data),
            role='user'  # Default role
        )
        
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('auth/register.html', form=form)

@app.route('/logout')
@login_required
def logout():
    # Clear the login role from session
    session.pop('login_as_role', None)
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

# Main routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/dashboard')
@login_required
def dashboard():
    # Get user statistics
    if current_user.role == 'user':
        # End user dashboard
        my_tickets = Ticket.query.filter_by(user_id=current_user.id)
        stats = {
            'total_tickets': my_tickets.count(),
            'open_tickets': my_tickets.filter_by(status='open').count(),
            'in_progress_tickets': my_tickets.filter_by(status='in_progress').count(),
            'resolved_tickets': my_tickets.filter_by(status='resolved').count()
        }
        recent_tickets = my_tickets.order_by(desc(Ticket.updated_at)).limit(5).all()
    else:
        # Agent/Admin dashboard
        all_tickets = Ticket.query
        if current_user.role == 'agent':
            # Agents see all tickets but with focus on assigned ones
            assigned_tickets = all_tickets.filter_by(assigned_to=current_user.id)
        else:
            assigned_tickets = all_tickets
        
        stats = {
            'total_tickets': all_tickets.count(),
            'open_tickets': all_tickets.filter_by(status='open').count(),
            'in_progress_tickets': all_tickets.filter_by(status='in_progress').count(),
            'my_assigned': assigned_tickets.count() if current_user.role == 'agent' else all_tickets.filter(Ticket.assigned_to.isnot(None)).count()
        }
        recent_tickets = all_tickets.order_by(desc(Ticket.updated_at)).limit(10).all()
    
    return render_template('dashboard.html', stats=stats, recent_tickets=recent_tickets)

@app.route('/tickets')
@login_required
def tickets_list():
    form = SearchForm()
    
    # Base query
    query = Ticket.query.options(
        joinedload(Ticket.creator),
        joinedload(Ticket.category),
        joinedload(Ticket.assignee)
    )
    
    # Apply filters based on form data
    if request.args.get('query'):
        search_term = f"%{request.args.get('query')}%"
        query = query.filter(
            or_(
                Ticket.subject.ilike(search_term),
                Ticket.description.ilike(search_term)
            )
        )
        form.query.data = request.args.get('query')
    
    if request.args.get('status'):
        query = query.filter(Ticket.status == request.args.get('status'))
        form.status.data = request.args.get('status')
    
    if request.args.get('category_id') and int(request.args.get('category_id')) > 0:
        query = query.filter(Ticket.category_id == int(request.args.get('category_id')))
        form.category_id.data = int(request.args.get('category_id'))
    
    if request.args.get('priority'):
        query = query.filter(Ticket.priority == request.args.get('priority'))
        form.priority.data = request.args.get('priority')
    
    if request.args.get('assigned_to') and int(request.args.get('assigned_to')) > 0:
        query = query.filter(Ticket.assigned_to == int(request.args.get('assigned_to')))
        form.assigned_to.data = int(request.args.get('assigned_to'))
    
    if request.args.get('my_tickets') == 'y':
        if current_user.role == 'user':
            query = query.filter(Ticket.user_id == current_user.id)
        else:
            query = query.filter(Ticket.assigned_to == current_user.id)
        form.my_tickets.data = True
    elif current_user.role == 'user':
        # Regular users only see their own tickets by default
        query = query.filter(Ticket.user_id == current_user.id)
    
    # Apply sorting
    sort_by = request.args.get('sort_by', 'created_desc')
    form.sort_by.data = sort_by
    
    if sort_by == 'created_asc':
        query = query.order_by(asc(Ticket.created_at))
    elif sort_by == 'updated_desc':
        query = query.order_by(desc(Ticket.updated_at))
    elif sort_by == 'updated_asc':
        query = query.order_by(asc(Ticket.updated_at))
    elif sort_by == 'votes_desc':
        query = query.order_by(desc(Ticket.upvotes - Ticket.downvotes))
    elif sort_by == 'comments_desc':
        query = query.outerjoin(TicketComment).group_by(Ticket.id).order_by(desc(func.count(TicketComment.id)))
    else:  # created_desc (default)
        query = query.order_by(desc(Ticket.created_at))
    
    # Pagination
    page = request.args.get('page', 1, type=int)
    tickets = query.paginate(page=page, per_page=20, error_out=False)
    
    return render_template('tickets/list.html', tickets=tickets, form=form)

@app.route('/tickets/create', methods=['GET', 'POST'])
@login_required
def create_ticket():
    form = TicketForm()
    
    if form.validate_on_submit():
        ticket = Ticket()
        ticket.subject = form.subject.data
        ticket.description = form.description.data
        ticket.category_id = form.category_id.data
        ticket.priority = form.priority.data
        ticket.user_id = current_user.id
        
        db.session.add(ticket)
        db.session.flush()  # Get the ticket ID
        
        # Handle file upload
        if form.attachment.data:
            file = form.attachment.data
            if allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # Add UUID to prevent filename conflicts
                unique_filename = f"{uuid.uuid4().hex}_{filename}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                file.save(file_path)
                
                # Create attachment record
                attachment = TicketAttachment()
                attachment.filename = unique_filename
                attachment.original_filename = filename
                attachment.file_size = get_file_size(file_path)
                attachment.mime_type = file.content_type or 'application/octet-stream'
                attachment.ticket_id = ticket.id
                attachment.uploaded_by = current_user.id
                db.session.add(attachment)
        
        db.session.commit()
        
        # Send notification email (mocked for MVP)
        send_notification_email(
            ticket,
            'new_ticket',
            f'New ticket created: {ticket.subject}'
        )
        
        flash('Ticket created successfully!', 'success')
        return redirect(url_for('view_ticket', id=ticket.id))
    
    return render_template('tickets/create.html', form=form)

@app.route('/tickets/<int:id>')
@login_required
def view_ticket(id):
    ticket = Ticket.query.get_or_404(id)
    
    # Check permissions
    if current_user.role == 'user' and ticket.user_id != current_user.id:
        abort(403)
    
    # Get comments (filter internal comments for regular users)
    all_comments = list(ticket.comments)
    if current_user.role == 'user':
        comments = [c for c in all_comments if not c.is_internal]
    else:
        comments = all_comments
    
    # Forms for actions
    update_form = TicketUpdateForm(obj=ticket)
    comment_form = CommentForm()
    vote_form = VoteForm()
    
    # Get user's vote
    user_vote = ticket.get_user_vote(current_user.id) if current_user.is_authenticated else None
    
    return render_template('tickets/view.html', 
                         ticket=ticket, 
                         comments=comments,
                         update_form=update_form,
                         comment_form=comment_form,
                         vote_form=vote_form,
                         user_vote=user_vote)

@app.route('/tickets/<int:id>/update', methods=['POST'])
@login_required
def update_ticket(id):
    ticket = Ticket.query.get_or_404(id)
    
    # Check permissions
    if not current_user.can_edit_ticket(ticket):
        abort(403)
    
    form = TicketUpdateForm()
    if form.validate_on_submit():
        # Track status changes
        old_status = ticket.status
        
        ticket.status = form.status.data
        ticket.priority = form.priority.data
        
        # Only agents/admins can assign tickets
        if current_user.can_assign_tickets():
            ticket.assigned_to = form.assigned_to.data if form.assigned_to.data > 0 else None
        
        # Update timestamps based on status changes
        if old_status != ticket.status:
            if ticket.status == 'resolved':
                ticket.resolved_at = datetime.utcnow()
            elif ticket.status == 'closed':
                ticket.closed_at = datetime.utcnow()
        
        db.session.commit()
        
        # Send notification email
        send_notification_email(
            ticket,
            'ticket_updated',
            f'Ticket updated: {ticket.subject}'
        )
        
        flash('Ticket updated successfully!', 'success')
    else:
        flash('Error updating ticket. Please check the form.', 'error')
    
    return redirect(url_for('view_ticket', id=id))

@app.route('/tickets/<int:id>/comment', methods=['POST'])
@login_required
def add_comment(id):
    ticket = Ticket.query.get_or_404(id)
    
    # Check permissions
    if current_user.role == 'user' and ticket.user_id != current_user.id:
        abort(403)
    
    form = CommentForm()
    if form.validate_on_submit():
        comment = TicketComment()
        comment.content = form.content.data
        comment.is_internal = form.is_internal.data and current_user.role in ['agent', 'admin']
        comment.ticket_id = ticket.id
        comment.user_id = current_user.id
        
        db.session.add(comment)
        ticket.updated_at = datetime.utcnow()
        db.session.commit()
        
        # Send notification email
        send_notification_email(
            ticket,
            'comment_added',
            f'New comment on ticket: {ticket.subject}'
        )
        
        flash('Comment added successfully!', 'success')
    else:
        flash('Error adding comment. Please check the form.', 'error')
    
    return redirect(url_for('view_ticket', id=id))

@app.route('/tickets/<int:id>/vote', methods=['POST'])
@login_required
def vote_ticket(id):
    ticket = Ticket.query.get_or_404(id)
    vote_type = request.form.get('vote_type')
    
    if vote_type not in ['up', 'down']:
        abort(400)
    
    # Check if user already voted
    existing_vote = TicketVote.query.filter_by(ticket_id=id, user_id=current_user.id).first()
    
    if existing_vote:
        if existing_vote.vote_type == vote_type:
            # Remove vote if clicking same vote type
            if vote_type == 'up':
                ticket.upvotes -= 1
            else:
                ticket.downvotes -= 1
            db.session.delete(existing_vote)
        else:
            # Change vote type
            if existing_vote.vote_type == 'up':
                ticket.upvotes -= 1
                ticket.downvotes += 1
            else:
                ticket.downvotes -= 1
                ticket.upvotes += 1
            existing_vote.vote_type = vote_type
    else:
        # Create new vote
        vote = TicketVote()
        vote.ticket_id = id
        vote.user_id = current_user.id
        vote.vote_type = vote_type
        db.session.add(vote)
        if vote_type == 'up':
            ticket.upvotes += 1
        else:
            ticket.downvotes += 1
    
    db.session.commit()
    
    if request.is_json:
        return jsonify({
            'upvotes': ticket.upvotes,
            'downvotes': ticket.downvotes,
            'user_vote': vote_type if not (existing_vote and existing_vote.vote_type == vote_type) else None
        })
    
    return redirect(url_for('view_ticket', id=id))

@app.route('/download/<int:attachment_id>')
@login_required
def download_file(attachment_id):
    attachment = TicketAttachment.query.get_or_404(attachment_id)
    ticket = attachment.ticket
    
    # Check permissions
    if current_user.role == 'user' and ticket.user_id != current_user.id:
        abort(403)
    
    return send_from_directory(app.config['UPLOAD_FOLDER'], 
                             attachment.filename, 
                             as_attachment=True,
                             download_name=attachment.original_filename)

# Admin routes
@app.route('/admin/categories')
@login_required
def admin_categories():
    if current_user.role != 'admin':
        abort(403)
    
    categories = Category.query.all()
    return render_template('admin/categories.html', categories=categories)

@app.route('/admin/categories/create', methods=['GET', 'POST'])
@login_required
def create_category():
    if current_user.role != 'admin':
        abort(403)
    
    form = CategoryForm()
    if form.validate_on_submit():
        # Check if category name already exists
        if Category.query.filter_by(name=form.name.data).first():
            flash('Category name already exists.', 'error')
            return render_template('admin/categories.html', form=form)
        
        category = Category()
        category.name = form.name.data
        category.description = form.description.data
        category.is_active = form.is_active.data
        
        db.session.add(category)
        db.session.commit()
        
        flash('Category created successfully!', 'success')
        return redirect(url_for('admin_categories'))
    
    categories = Category.query.all()
    return render_template('admin/categories.html', categories=categories, form=form)

@app.route('/admin/categories/<int:id>/edit', methods=['POST'])
@login_required
def edit_category(id):
    if current_user.role != 'admin':
        abort(403)
    
    category = Category.query.get_or_404(id)
    form = CategoryForm()
    
    if form.validate_on_submit():
        # Check if new name conflicts with existing category
        existing = Category.query.filter(Category.name == form.name.data, Category.id != id).first()
        if existing:
            flash('Category name already exists.', 'error')
        else:
            category.name = form.name.data
            category.description = form.description.data
            category.is_active = form.is_active.data
            
            db.session.commit()
            flash('Category updated successfully!', 'success')
    
    return redirect(url_for('admin_categories'))

@app.route('/admin/users')
@login_required
def admin_users():
    if current_user.role != 'admin':
        abort(403)
    
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@app.route('/admin/users/<int:id>/edit', methods=['POST'])
@login_required
def edit_user(id):
    if current_user.role != 'admin':
        abort(403)
    
    user = User.query.get_or_404(id)
    form = UserEditForm()
    
    if form.validate_on_submit():
        # Check for username/email conflicts
        username_conflict = User.query.filter(User.username == form.username.data, User.id != id).first()
        email_conflict = User.query.filter(User.email == form.email.data, User.id != id).first()
        
        if username_conflict:
            flash('Username already exists.', 'error')
        elif email_conflict:
            flash('Email already exists.', 'error')
        else:
            user.username = form.username.data
            user.email = form.email.data
            user.first_name = form.first_name.data
            user.last_name = form.last_name.data
            user.role = form.role.data
            user.is_active = form.is_active.data
            
            db.session.commit()
            flash('User updated successfully!', 'success')
    
    return redirect(url_for('admin_users'))

# Error handlers
@app.errorhandler(403)
def forbidden(error):
    return render_template('errors/403.html'), 403

@app.errorhandler(404)
def not_found(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('errors/500.html'), 500

# Context processors
@app.context_processor
def inject_user():
    return dict(current_user=current_user)

@app.context_processor
def utility_processor():
    def format_datetime(dt):
        if dt:
            return dt.strftime('%Y-%m-%d %H:%M')
        return ''
    
    def get_ticket_count():
        if current_user.is_authenticated:
            if current_user.role == 'user':
                return Ticket.query.filter_by(user_id=current_user.id).count()
            else:
                return Ticket.query.count()
        return 0
    
    return dict(format_datetime=format_datetime, get_ticket_count=get_ticket_count)
