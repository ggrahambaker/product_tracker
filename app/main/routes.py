
from flask import render_template, flash, redirect, url_for, request, current_app, g
from werkzeug.urls import url_parse
from app import db

from app.main.forms import EditProfileForm, MakeAssetForm, MakeCommentForm, SearchForm, EditAssetForm
from app.models import User, FinAsset, FinComment

from flask_login import current_user, login_required

from datetime import datetime

from app.main import bp

@bp.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()
        g.search_form = SearchForm()



@bp.route('/')
@bp.route('/index')
@login_required
def index():
    page = request.args.get('page', 1, type=int)

    assets = FinAsset.query.order_by(FinAsset.last_active.desc()).paginate(
        page, current_app.config['POSTS_PER_PAGE'], False
    )


    next_url = url_for('main.index', page = assets.next_num) if assets.has_next else None
    prev_url = url_for('main.index', page = assets.prev_num) if assets.has_prev else None

    return render_template('index.html', title='home', assets = assets.items, next_url = next_url, prev_url = prev_url)





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

@bp.route('/edit_asset/<assetname>', methods=['GET', 'POST'])
@login_required
def edit_asset(assetname):
    asset = FinAsset.query.filter_by(name = assetname).first_or_404()
    form = EditAssetForm(assetname)

    if form.validate_on_submit():
        asset.name = form.title.data
        asset.description = form.description.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('main.assets',  assetname=asset.name))
    elif request.method == 'GET':
        form.title.data = asset.name
        form.description.data = asset.description
    return render_template('edit_profile.html', title='Edit Profile',
                           form=form)

@bp.route('/search')
@login_required
def search():
    if not g.search_form.validate():
        return redirect(url_for('main.index'))
    page = request.args.get('page', 1, type=int)
    assets, total = FinAsset.search(g.search_form.q.data, page,
                               current_app.config['POSTS_PER_PAGE'])
    next_url = url_for('main.search', q=g.search_form.q.data, page=page + 1) \
        if total > page * current_app.config['POSTS_PER_PAGE'] else None
    prev_url = url_for('main.search', q=g.search_form.q.data, page=page - 1) \
        if page > 1 else None
    return render_template('search.html', title='Search', assets=assets,
                           next_url=next_url, prev_url=prev_url)
