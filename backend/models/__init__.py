from flask_sqlalchemy import SQLAlchemy

# Global SQLAlchemy instance

db = SQLAlchemy()

# --- Models ---

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(80))
    created_at = db.Column(db.DateTime, server_default=db.func.now())


class AgentTask(db.Model):
    __tablename__ = 'agent_tasks'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    agent_id = db.Column(db.String(50), nullable=False)
    input = db.Column(db.Text)
    output = db.Column(db.Text)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    user = db.relationship('User', backref=db.backref('tasks', lazy=True))
