from flask_wtf import Form
from wtforms import FileField, StringField, SubmitField, SelectMultipleField
from wtforms.validators import DataRequired


class UploadForm(Form):
    file = FileField('file', validators=[DataRequired()])
    version = StringField('version', validators=[DataRequired()])
    author = StringField('author', validators=[DataRequired()])


class PartSearchForm(Form):
    manufacturer = SelectMultipleField('Manufacturer',
                                       validators=[DataRequired()])
    manufacturer_part_number = StringField('Manufacturer Part Number',
                                           validators=[DataRequired()])
    submit = SubmitField('Search!')
