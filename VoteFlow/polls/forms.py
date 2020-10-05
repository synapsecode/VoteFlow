from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, FileField, BooleanField, TextAreaField, SelectField
from wtforms.validators import DataRequired, EqualTo, Email, ValidationError
from wtforms_components import ColorField
#Forms related to User Functionality i.e Logins, Register etc

class NewPollForm(FlaskForm):
	submit = SubmitField('+')

class EditFlaggedUsernameForm(FlaskForm):
	submit = SubmitField('Update Usernames')

class CreatePollForm(FlaskForm):
	poll_name = StringField('Poll Name', validators=[DataRequired()])
	poll_type = SelectField(
        'Poll Type',
        choices=[
            ('A2A', 'Completely Open Elections'),
            ('G-I2I', 'Gender Based Elections'),
            ('H-I2I', 'House Based Elections'),
            ('GH-I2I', 'House and Gender Based Elections'),
        ]
    )
	houses = TextAreaField('Houses')
	positions = TextAreaField('Positions', validators=[DataRequired()])
	year = StringField('Year', validators=[DataRequired()])
	submit = SubmitField('Create Poll')

class AddStudentsForm(FlaskForm):
    students = FileField()
    submit = SubmitField('Upload DataFile')

class AddNomineesForm(FlaskForm):
    nominees = FileField()
    nominees_logo = FileField()
    submit = SubmitField('Upload Data')