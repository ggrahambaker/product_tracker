
from flask import render_template, flash, redirect, url_for, request
from app.forms import LoginForm


from app import app


@app.route('/')
@app.route('/index')
def index():
    user = {'username': 'graham'}


    return render_template('index.html', title= 'home', user=user)



@app.route('/login', methods = ['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        flash('login requested for username: {}, remember_me: {}'.format(
            form.username.data, form.remember_me.data)
            )
        redirect(url_for('index'))

    return render_template('login.html', title = 'login', form=form)