from wtforms import Form, StringField, PasswordField, validators, SubmitField, SelectField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Length
from app.models import User


def validate_email(self, email):
        """Email validation"""
        user = User.find_by_emailaddress(email)
        if user is not None:
            raise ValidationError("It seems like that email address is in use.")

class SignupForm(Form):
    """User signup form"""
    email = StringField("Email", validators=[Length(min=6, message=(u'Too short for an email address.')),
            Email(message=('That does not look like an email address.')),
            DataRequired(message=('Please enter an email address.')), validate_email])
    password = PasswordField('Password', validators=[DataRequired(message="Please enter a password")])
    confirmPassword = PasswordField('Repeat Password', validators=[
        EqualTo(password, message='Passwords must match.')])
    submit = SubmitField('Register')

    
