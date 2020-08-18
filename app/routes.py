
from flask import render_template, flash, redirect, url_for, request
from werkzeug.urls import url_parse

from flask_login import login_user, current_user, logout_user, login_required
from app.forms import LoginForm, RegistrationForm, EditProfileForm, MakeAssetForm, MakeCommentForm
from app.models import User, FinAsset, FinComment

from app import app, db
from datetime import datetime

@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()


@app.route('/')
@app.route('/index')
@login_required
def index():
    assets = FinAsset.query.order_by(FinAsset.last_active.desc()).all()

    return render_template('index.html', title= 'home', assets = assets)



@app.route('/login', methods = ['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username = form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('invalid username or password')
            return redirect(url_for('login'))


        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')

        return redirect(next_page)


    return render_template('login.html', title = 'login', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))



@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('user', username = current_user.username))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Edit Profile',
                           form=form)


@app.route('/user/<username>')
def user(username):
    user = User.query.filter_by(username=username).first_or_404()

    return render_template('user.html', user=user)


@app.route('/new_asset', methods = ['GET', 'POST'])
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
        return redirect(url_for('assets', assetname=asset.name))
    
    return render_template('new_asset.html', title='Create New Asset Page', form=form)


    

@app.route('/assets/<assetname>', methods = ['GET', 'POST'])
@login_required
def assets(assetname):
    asset = FinAsset.query.filter_by(name = assetname).first_or_404()

    comments = FinComment.query.filter_by(asset = asset).order_by(FinComment.created_at.desc()).all()
    form = MakeCommentForm()

    if form.validate_on_submit():




        comment = FinComment(body = form.comment.data, 
                            asset = asset,
                            author = current_user)
        

        ## also update Asset timestamp for sorting
        asset.last_active = datetime.utcnow()
    
        db.session.add(comment)
        db.session.commit()
        flash('comment posted!')
        return redirect(url_for('assets', assetname=asset.name))

    return render_template('asset.html', form=form, asset_obj = asset, comments = comments)