from flask_wtf import Form
from wtforms import (FileField, StringField, SubmitField, SelectMultipleField,
                     PasswordField, BooleanField)
from wtforms.validators import DataRequired, Email


class UploadForm(Form):
    file_ = FileField('file', validators=[DataRequired()])
    name = StringField('Project Name', validators=[DataRequired()])
    version = StringField('Version', validators=[DataRequired()])


class RegisterUserForm(Form):
    name = StringField('Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])


class LoginForm(Form):
    email = StringField('Email:', validators=[DataRequired(), Email()])
    password = PasswordField('Password:', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me?')


class PartSearchForm(Form):
    manufacturer = SelectMultipleField('Manufacturer',
                                       validators=[DataRequired()])
    manufacturer_part_number = StringField('Manufacturer Part Number',
                                           validators=[DataRequired()])
    submit = SubmitField('Search!')


class BOMActionForm(Form):
    download = SubmitField('Download KiCAD Archive')
    update = SubmitField('Lookup/Refresh Part Information')
