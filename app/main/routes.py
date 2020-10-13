
from flask import render_template, flash, redirect, url_for, request, current_app, g, jsonify
from werkzeug.urls import url_parse
from werkzeug.utils import secure_filename
from app import db
import os
from app.main.forms import EditProfileForm, MakeAssetForm, MakeCommentForm, SearchForm, EditAssetForm, MessageForm
from app.models import User, FinAsset, FinComment, Message, Notification, FinAssetAttachment

from flask_login import current_user, login_required
from app.upload import upload_file_to_s3

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
@login_required
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

  
        if len(form.files.data) > 0:
            for file in form.files.data:
                filename = secure_filename(file.filename)
                if filename == '':
                    break
                s3_filepath = upload_file_to_s3(file, filename)
                ##file.save(os.path.join(current_app.config['UPLOAD_PATH'], filename))
                att = FinAssetAttachment(name=filename, url=s3_filepath, asset = asset)
                db.session.add(att)
        

    
        db.session.commit()

        flash('created new asset page')
        return redirect(url_for('main.assets', assetname=asset.name))
    
    return render_template('new_asset.html', title='Create New Asset Page', form=form)


    

@bp.route('/assets/<assetname>', methods = ['GET', 'POST'])
@login_required
def assets(assetname):
    asset = FinAsset.query.filter_by(name = assetname).first_or_404()

    comments = FinComment.query.filter_by(asset = asset).order_by(FinComment.created_at.desc()).all()
    attach = FinAssetAttachment.query.filter_by(asset = asset).all()
    if not attach:
        attach = None
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

    return render_template('asset.html', form=form, asset_obj = asset, comments = comments, attach = attach)


@bp.route('/delete_comment/<comment_id>')
@login_required
def delete_comment(comment_id):
    comment = FinComment.query.get(comment_id)
    
    if not comment:
        flash('an error has occured deleting comment')

        asset = FinAsset.query.get(comment.asset_id)
        return redirect(url_for('main.assets', assetname=asset.name))

    db.session.delete(comment)
    db.session.commit()

    asset = FinAsset.query.get(comment.asset_id)
    return redirect(url_for('main.assets', assetname=asset.name))


    

@bp.route('/edit_asset/<assetname>', methods=['GET', 'POST'])
@login_required
def edit_asset(assetname):
    asset = FinAsset.query.filter_by(name = assetname).first_or_404()
    form = EditAssetForm(assetname)

    if form.validate_on_submit():
        asset.name = form.title.data
        asset.description = form.description.data
        if len(form.files.data) > 0:
            for file in form.files.data:
                filename = secure_filename(file.filename)
                if filename == '':
                    break
                file.save(os.path.join(current_app.config['UPLOAD_PATH'], filename))
                att = FinAssetAttachment(name=filename, asset = asset)
                db.session.add(att)


        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('main.assets',  assetname=asset.name))
    elif request.method == 'GET':
        form.title.data = asset.name
        form.description.data = asset.description

        attach = FinAssetAttachment.query.filter_by(asset = asset).all()
        

    return render_template('edit_asset.html', title='Edit Asset',
                           form=form, attach=attach)



@bp.route('/delete_attachment/<attach_id>', methods = ['POST'])
@login_required
def delete_attachment(attach_id):
    attach = FinAssetAttachment.query.get(attach_id)
    
    if not attach:
        flash('an error has occured deleting attachment')

        asset = FinAsset.query.get(attach.asset_id)
        return redirect(url_for('main.index'))

    asset = FinAsset.query.get(attach.asset.id)
    
    db.session.delete(attach)
    db.session.commit()
    os.remove(os.path.join(current_app.config['UPLOAD_PATH'], attach.name))

    return redirect(url_for('main.edit_asset', assetname=asset.name))



@bp.route('/follow/<assetname>')
@login_required
def follow(assetname):
    print(assetname)
    asset = FinAsset.query.filter_by(name = assetname).first()
    if asset is None:
        flash('Asset {} not found'.format(assetname))
        return redirect( url_for('main.index'))

    current_user.follow_asset(asset)
    db.session.commit()
    flash('you are now following {}'.format(assetname))
    return redirect(url_for('main.assets', assetname = assetname))




@bp.route('/unfollow/<assetname>')
@login_required
def unfollow(assetname):
    asset = FinAsset.query.filter_by(name = assetname).first()
    if asset is None:
        flash('Asset {} not found'.format(assetname))
        return redirect( url_for('main.index'))

    current_user.unfollow_asset(asset)
    db.session.commit()
    flash('you are not following {}'.format(assetname))
    return redirect(url_for('main.assets', assetname = assetname))


@bp.route('/followed_assets')
@login_required
def followed_assets():
    user = User.query.filter_by(username = current_user.username).first()
    assets = user.get_followed_assets()

    page = request.args.get('page', 1, type=int)

    assets_ord = assets.order_by(FinAsset.last_active.desc()).paginate(
        page, current_app.config['POSTS_PER_PAGE'], False
    )


    next_url = url_for('main.index', page = assets_ord.next_num) if assets_ord.has_next else None
    prev_url = url_for('main.index', page = assets_ord.prev_num) if assets_ord.has_prev else None

    return render_template('index.html', title='followed', assets = assets_ord.items, next_url = next_url, prev_url = prev_url)



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



@bp.route('/send_message/<recipient>', methods=['GET', 'POST'])
@login_required
def send_message(recipient):
    user = User.query.filter_by(username=recipient).first_or_404()
    form = MessageForm()
    if form.validate_on_submit():

        user.add_notification('unread_message_count', user.new_messages())
        
        msg = Message(author=current_user, recipient=user,
                      body=form.message.data)
        db.session.add(msg)
        db.session.commit()
        flash('Your message has been sent.')
        return redirect(url_for('main.user', username=recipient))
    return render_template('send_message.html', title='Send Message',
                           form=form, recipient=recipient)


@bp.route('/messages')
@login_required
def messages():
    current_user.last_message_read_time = datetime.utcnow()
    current_user.add_notification('unread_message_count', 0)
    db.session.commit()
    page = request.args.get('page', 1, type=int)
    messages = current_user.messages_received.order_by(
        Message.timestamp.desc()).paginate(
            page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.messages', page=messages.next_num) \
        if messages.has_next else None
    prev_url = url_for('main.messages', page=messages.prev_num) \
        if messages.has_prev else None
    return render_template('messages.html', messages=messages.items,
                           next_url=next_url, prev_url=prev_url)



@bp.route('/notifications')
@login_required
def notifications():
    since = request.args.get('since', 0.0, type=float)
    notifications = current_user.notifications.filter(
        Notification.timestamp > since).order_by(Notification.timestamp.asc())
    return jsonify([{
        'name': n.name,
        'data': n.get_data(),
        'timestamp': n.timestamp
    } for n in notifications])



@bp.route('/export_posts')
@login_required
def export_posts():
    if current_user.get_task_in_progress('export_posts'):
        flash('An export task is currently in progress')
    else:
        current_user.launch_task('export_posts','Exporting posts...')
        db.session.commit()
    return redirect(url_for('main.user', username=current_user.username))
    