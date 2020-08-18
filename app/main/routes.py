
from flask import render_template, flash, redirect, url_for, request
from werkzeug.urls import url_parse
from app import db

from app.main.forms import EditProfileForm, MakeAssetForm, MakeCommentForm
from app.models import User, FinAsset, FinComment

from flask_login import current_user, login_required

from datetime import datetime

from app.main import bp

@bp.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()


@bp.route('/')
@bp.route('/index')
@login_required
def index():
    assets = FinAsset.query.order_by(FinAsset.last_active.desc()).all()

    return render_template('index.html', title= 'home', assets = assets)





@bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('auth.user', username = current_user.username))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Edit Profile',
                           form=form)


@bp.route('/user/<username>')
def user(username):
    user = User.query.filter_by(username=username).first_or_404()

    return render_template('user.html', user=user)


@bp.route('/new_asset', methods = ['GET', 'POST'])
@login_required
def new_asset():
    form = MakeAssetForm()

    if form.validate_on_submit():
        asset = FinAsset(name=form.title.data, 
                         description=form.description.data,
                         owner=current_user)
        db.session.add(asset)
        db.session.commit()
        flash('created new asset page')
        return redirect(url_for('main.assets', assetname=asset.name))
    
    return render_template('new_asset.html', title='Create New Asset Page', form=form)


    

@bp.route('/assets/<assetname>', methods = ['GET', 'POST'])
@login_required
def assets(assetname):
    asset = FinAsset.query.filter_by(name = assetname).first_or_404()

    comments = FinComment.query.filter_by(asset = asset).order_by(FinComment.created_at.desc()).all()
    form = MakeCommentForm()

    if form.validate_on_submit():

        comment = FinComment(body = form.comment.data, 
                            asset = asset,
                            author = current_user)
    
        asset.last_active = datetime.utcnow()
    
        db.session.add(comment)
        db.session.commit()
        flash('comment posted!')
        return redirect(url_for('main.assets', assetname=asset.name))

    return render_template('asset.html', form=form, asset_obj = asset, comments = comments)