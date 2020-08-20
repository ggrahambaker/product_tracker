from flask import request
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, ValidationError, Email, EqualTo, Length
from app.models import User, FinAsset



class EditProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    about_me = TextAreaField('About me', validators=[Length(min=0, max=140)])

    def __init__(self, original_username, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=self.username.data).first()
            if user is not None:
                raise ValidationError('Please use a different username.')

    
    submit = SubmitField('Submit')

class MakeAssetForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[Length(min=0, max=140), DataRequired()])

    submit = SubmitField('Make New Page')


class EditAssetForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[Length(min=0, max=140)])
    
    def __init__(self, original_asset_name, *args, **kwargs):
        super(EditAssetForm, self).__init__(*args, **kwargs)
        self.original_asset_name = original_asset_name


    def validate_title(self, asset):
        print(asset)
        if asset.data != self.original_asset_name:
            asset = FinAsset.query.filter_by(name=self.title.data).first()
            if asset is not None:
                raise ValidationError('Please use a different asset name.')

    submit = SubmitField('Edit Page')

class MakeCommentForm(FlaskForm):
    comment = TextAreaField('Comment', validators=[Length(min=0, max=140)])
    submit = SubmitField('submit')


class SearchForm(FlaskForm):
    q = StringField('Search', validators=[DataRequired()])
    def __init__(self, *args, **kwargs):
        if 'formdata' not in kwargs:
            kwargs['formdata'] = request.args
        if 'csrf_enabled' not in kwargs:
            kwargs['csrf_enabled'] = False

        super(SearchForm, self).__init__(*args, **kwargs)