# coding=utf-8

from flask_wtf import FlaskForm
import wtforms
from wtforms.validators import DataRequired, Optional


class CreateProjectForm(FlaskForm):
    name = wtforms.StringField('name', validators=[DataRequired()])
    workdir = wtforms.StringField('workdir', validators=[DataRequired()])
    build_command = wtforms.StringField('build_command', validators=[DataRequired()])
    quickcheck_command = wtforms.StringField('quickcheck_command', validators=[Optional()])
    quickcheck_timeout = wtforms.FloatField('quickcheck_timeout', validators=[Optional()])
    test_command = wtforms.StringField('test_command', validators=[DataRequired()])
    test_timeout = wtforms.FloatField('test_timeout', validators=[Optional()])
    clean_command = wtforms.StringField('clean_command', validators=[Optional()])


class CreateFileForm(FlaskForm):
    filename = wtforms.StringField('filename', validators=[DataRequired()])


class SetConfirmationForm(FlaskForm):
    confirmation = wtforms.RadioField('comfirmation', choices=[('unknown', 'unknown'),
                                                               ('confirmed', 'confirmed'),
                                                               ('ignored', 'ignored')])
