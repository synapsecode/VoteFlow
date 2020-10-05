# Imports
from datetime import datetime
from flask import current_app
from VoteFlow import db, school_login_manager
from flask_login import UserMixin

# Initiate Login Managers
@school_login_manager.user_loader
def load_user(user_id):
	return School.query.get(int(user_id))

class School(UserMixin, db.Model):
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String, unique=True, nullable=False)
	schoolname = db.Column(db.String, unique=True, nullable=False)
	school_abbr = db.Column(db.String, unique=True, nullable=False)
	email = db.Column(db.String, unique=True, nullable=False)
	password = db.Column(db.String, unique=True, nullable=False)
	school_logo = db.Column(db.String, nullable=False)
	accent_color = db.Column(db.String, nullable=False)

	def __repr__(self):
		return f"School('{self.schoolname}', '{self.school_abbr}', '{self.username}')"


class Student(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	school = db.Column(db.String, nullable=False)
	poll = db.Column(db.String, nullable=False)
	full_name = db.Column(db.String, nullable=False)
	username = db.Column(db.String, nullable=False)
	password = db.Column(db.String, nullable=False)
	grade = db.Column(db.Integer, nullable=False)
	section = db.Column(db.String, nullable=False)
	roll_no = db.Column(db.String, nullable=False)
	gender = db.Column(db.String, nullable=True)
	house = db.Column(db.String, nullable=True)
	voted = db.Column(db.Boolean)

	def __repr__(self):
		return f"Student('{self.school}', '{self.full_name}')"


class Nominee(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	school = db.Column(db.String, nullable=False)
	poll = db.Column(db.String, nullable=False)
	full_name = db.Column(db.String, nullable=False)
	post = db.Column(db.String, nullable=False)
	house = db.Column(db.String, nullable=True)
	gender = db.Column(db.String, nullable=True)
	logo = db.Column(db.String, nullable=True, default="default.jpg")
	slogan = db.Column(db.String, nullable=False)
	votes = db.Column(db.Integer)

class Poll(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	host = db.Column(db.String, nullable=False)
	poll_name = db.Column(db.String, nullable=False)
	poll_type = db.Column(db.String, nullable=False)
	# election_date = db.Column(db.String, nullable=False)
	houses = db.Column(db.PickleType, nullable=True)
	positions = db.Column(db.PickleType, nullable=False)
	year = db.Column(db.String, nullable=False)
	status = db.Column(db.String, nullable=False)

	def __repr__(self):
		return f"Poll('{self.poll_name}', '{self.host}', '{self.year}')"

class FlaggedStudent(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	student_id = db.Column(db.Integer, db.ForeignKey('student.id'))
	poll_id = db.Column(db.Integer, db.ForeignKey('poll.id'))
	school_id = db.Column(db.Integer, db.ForeignKey('school.id'))

class Results(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	school = db.Column(db.String, nullable=False)
	poll = db.Column(db.String, nullable=False)
	full_name = db.Column(db.String, nullable=False)
	post = db.Column(db.String, nullable=False)
	votes = db.Column(db.Integer)
