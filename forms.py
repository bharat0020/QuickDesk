from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, SelectField, PasswordField, BooleanField, HiddenField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional
from wtforms.widgets import TextArea
from models import Category, User

class LoginForm(FlaskForm):
    username = StringField('Username or Email', validators=[DataRequired(), Length(min=3, max=80)])
    password = PasswordField('Password', validators=[DataRequired()])
    role = SelectField('Login As', choices=[
        ('user', 'End User'),
        ('agent', 'Support Agent'),
        ('admin', 'Administrator')
    ], default='user', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    first_name = StringField('First Name', validators=[DataRequired(), Length(min=1, max=50)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(min=1, max=50)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    password_confirm = PasswordField('Confirm Password', 
                                   validators=[DataRequired(), EqualTo('password')])

class TicketForm(FlaskForm):
    subject = StringField('Subject', validators=[DataRequired(), Length(min=5, max=200)])
    description = TextAreaField('Description', validators=[DataRequired(), Length(min=10)], 
                               widget=TextArea(), render_kw={"rows": 6})
    category_id = SelectField('Category', coerce=int, validators=[DataRequired()])
    priority = SelectField('Priority', choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ], default='medium')
    attachment = FileField('Attachment', validators=[
        FileAllowed(['txt', 'pdf', 'doc', 'docx', 'xls', 'xlsx', 'png', 'jpg', 'jpeg', 'gif'], 
                   'Only documents and images are allowed!')
    ])
    
    def __init__(self, *args, **kwargs):
        super(TicketForm, self).__init__(*args, **kwargs)
        self.category_id.choices = [(c.id, c.name) for c in Category.query.filter_by(is_active=True).all()]

class TicketUpdateForm(FlaskForm):
    status = SelectField('Status', choices=[
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed')
    ])
    assigned_to = SelectField('Assign To', coerce=int, validators=[Optional()])
    priority = SelectField('Priority', choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ])
    
    def __init__(self, *args, **kwargs):
        super(TicketUpdateForm, self).__init__(*args, **kwargs)
        # Only agents and admins can be assigned tickets
        agents = User.query.filter(User.role.in_(['agent', 'admin'])).all()
        self.assigned_to.choices = [(0, 'Unassigned')] + [(a.id, a.full_name) for a in agents]

class CommentForm(FlaskForm):
    content = TextAreaField('Comment', validators=[DataRequired(), Length(min=1)], 
                          widget=TextArea(), render_kw={"rows": 4})
    is_internal = BooleanField('Internal Comment (visible only to agents/admins)')

class CategoryForm(FlaskForm):
    name = StringField('Category Name', validators=[DataRequired(), Length(min=3, max=100)])
    description = TextAreaField('Description', validators=[Optional()], 
                               widget=TextArea(), render_kw={"rows": 3})
    is_active = BooleanField('Active', default=True)

class UserEditForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    first_name = StringField('First Name', validators=[DataRequired(), Length(min=1, max=50)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(min=1, max=50)])
    role = SelectField('Role', choices=[
        ('user', 'End User'),
        ('agent', 'Support Agent'),
        ('admin', 'Administrator')
    ])
    is_active = BooleanField('Active', default=True)

class SearchForm(FlaskForm):
    query = StringField('Search', validators=[Optional()])
    status = SelectField('Status', choices=[
        ('', 'All Statuses'),
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed')
    ], default='')
    category_id = SelectField('Category', coerce=int, validators=[Optional()])
    priority = SelectField('Priority', choices=[
        ('', 'All Priorities'),
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ], default='')
    assigned_to = SelectField('Assigned To', coerce=int, validators=[Optional()])
    my_tickets = BooleanField('My Tickets Only')
    sort_by = SelectField('Sort By', choices=[
        ('created_desc', 'Newest First'),
        ('created_asc', 'Oldest First'),
        ('updated_desc', 'Recently Updated'),
        ('updated_asc', 'Least Recently Updated'),
        ('votes_desc', 'Most Voted'),
        ('comments_desc', 'Most Commented')
    ], default='created_desc')
    
    def __init__(self, *args, **kwargs):
        super(SearchForm, self).__init__(*args, **kwargs)
        self.category_id.choices = [(0, 'All Categories')] + [(c.id, c.name) for c in Category.query.filter_by(is_active=True).all()]
        agents = User.query.filter(User.role.in_(['agent', 'admin'])).all()
        self.assigned_to.choices = [(0, 'All Assignees')] + [(a.id, a.full_name) for a in agents]

class VoteForm(FlaskForm):
    ticket_id = HiddenField('Ticket ID', validators=[DataRequired()])
    vote_type = HiddenField('Vote Type', validators=[DataRequired()])
