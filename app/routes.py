
from flask import render_template, flash, redirect, url_for, request
from app.forms import LoginForm


from app import app


@app.route('/')
@app.route('/index')
def index():
    user = {'username': 'graham'}


    return render_template('index.html', title= 'home', user=user)



@app.route('/login')
def login():
    form = LoginForm()
    return render_template('login.html', title = 'login', form=form)