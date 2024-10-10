from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app import app, db
from app import User, Poll, PollOption, Vote
from sqlalchemy import func

@app.route('/')
def index():
    polls = Poll.query.all()
    return render_template('index.html', polls=polls)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('index'))
        flash('Invalid email or password')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email already exists')
        else:
            new_user = User(email=email, password_hash=generate_password_hash(password))
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            return redirect(url_for('index'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/create_poll', methods=['GET', 'POST'])
@login_required
def create_poll():
    if request.method == 'POST':
        title = request.form.get('title')
        options = request.form.getlist('options')
        new_poll = Poll(title=title, user_id=current_user.user_id)
        db.session.add(new_poll)
        db.session.flush()  # This will assign an ID to new_poll
        for option_text in options:
            if option_text.strip():  # Only add non-empty options
                new_option = PollOption(poll_id=new_poll.poll_id, option_text=option_text)
                db.session.add(new_option)
        db.session.commit()
        flash('Poll created successfully!')
        return redirect(url_for('index'))
    return render_template('create_poll.html')

@app.route('/poll/<int:poll_id>')
def view_poll(poll_id):
    poll = Poll.query.get_or_404(poll_id)
    #options = PollOption.query.filter_by(poll_id=poll_id).all()
    options_with_votes = db.session.query(
        PollOption,
        func.count(Vote.vote_id).label('vote_count')
    ).outerjoin(Vote).filter(PollOption.poll_id == poll_id).group_by(PollOption.option_id).all()
    

    return render_template('view_poll.html', poll=poll, options_with_votes=options_with_votes)



@app.route('/vote/<int:poll_id>', methods=['POST'])
def vote(poll_id):
    option_id = request.form.get('option')
    ip_address = request.remote_addr
    existing_vote = Vote.query.filter_by(poll_id=poll_id, ip_address=ip_address).first()
    # if existing_vote:
    #     flash('You have already voted on this poll')
    # else:
    new_vote = Vote(poll_id=poll_id, option_id=option_id, ip_address=ip_address)
    db.session.add(new_vote)
    db.session.commit()
    flash('Your vote has been recorded')
    return redirect(url_for('view_poll', poll_id=poll_id))
