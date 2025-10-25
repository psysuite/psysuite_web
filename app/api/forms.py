from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length, Optional, NumberRange
from flask_wtf.file import FileField, FileRequired, FileAllowed

class MobileApplicationForm(FlaskForm):
    version = IntegerField('Version Code', 
                          validators=[DataRequired(), NumberRange(min=1, max=999999)],
                          render_kw={"placeholder": "e.g., 61"})
    sver = StringField('Version String', 
                      validators=[DataRequired(), Length(min=1, max=40)],
                      render_kw={"placeholder": "e.g., 1.2.3"})
    description = TextAreaField('Description', 
                               validators=[Optional(), Length(max=500)], 
                               render_kw={"rows": 5, "placeholder": "What's new in this version..."})
    apk = FileField('APK File', 
                   validators=[FileRequired(), FileAllowed(['apk'], 'APK files only!')])
    submit = SubmitField('Upload New Version')