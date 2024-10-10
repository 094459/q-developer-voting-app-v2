from flask import Flask, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:change-me@127.0.0.1/voting'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key')
db = SQLAlchemy(app)


# Models
class User(db.Model):
    __tablename__ = 'users'
    user_id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Poll(db.Model):
    __tablename__ = 'polls'
    poll_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    title = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class PollOption(db.Model):
    __tablename__ = 'poll_options'
    option_id = db.Column(db.Integer, primary_key=True)
    poll_id = db.Column(db.Integer, db.ForeignKey('polls.poll_id'))
    option_text = db.Column(db.String(255), nullable=False)

class Vote(db.Model):
    __tablename__ = 'votes'
    vote_id = db.Column(db.Integer, primary_key=True)
    poll_id = db.Column(db.Integer, db.ForeignKey('polls.poll_id'))
    option_id = db.Column(db.Integer, db.ForeignKey('poll_options.option_id'))
    ip_address = db.Column(db.String(45), nullable=False)
    voted_at = db.Column(db.DateTime, default=datetime.utcnow)

# Routes
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    if User.query.filter_by(email=email).first():
        return jsonify({'message': 'Email already registered'}), 400
    
    new_user = User(email=email, password_hash=generate_password_hash(password))
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({'message': 'User registered successfully'}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    user = User.query.filter_by(email=email).first()
    if user and check_password_hash(user.password_hash, password):
        session['user_id'] = user.user_id
        return jsonify({'message': 'Logged in successfully'}), 200
    
    return jsonify({'message': 'Invalid credentials'}), 401

@app.route('/create_poll', methods=['POST'])
def create_poll():
    if 'user_id' not in session:
        return jsonify({'message': 'Please login first'}), 401
    
    data = request.json
    title = data.get('title')
    options = data.get('options', [])
    
    new_poll = Poll(user_id=session['user_id'], title=title)
    db.session.add(new_poll)
    db.session.flush()
    
    for option in options:
        new_option = PollOption(poll_id=new_poll.poll_id, option_text=option)
        db.session.add(new_option)
    
    db.session.commit()
    
    return jsonify({'message': 'Poll created successfully', 'poll_id': new_poll.poll_id}), 201

@app.route('/vote/<int:poll_id>', methods=['POST'])
def vote(poll_id):
    data = request.json
    option_id = data.get('option_id')
    ip_address = request.remote_addr
    
    existing_vote = Vote.query.filter_by(poll_id=poll_id, ip_address=ip_address).first()
    if existing_vote:
        return jsonify({'message': 'You have already voted on this poll'}), 400
    
    db.session.add(new_vote)
    db.session.commit()
    
    return jsonify({'message': 'Vote recorded successfully'}), 201

@app.route('/poll_results/<int:poll_id>', methods=['GET'])
def poll_results(poll_id):
    poll = Poll.query.get_or_404(poll_id)
    options = PollOption.query.filter_by(poll_id=poll_id).all()
    
    results = []
    for option in options:
        vote_count = Vote.query.filter_by(poll_id=poll_id, option_id=option.option_id).count()
        results.append({
            'option': option.option_text,
            'votes': vote_count
        })
    
    return jsonify({
        'poll_title': poll.title,
        'results': results
    }), 200

if __name__ == '__main__':
    app.run(debug=True)
