# imports
from flask import render_template, request, Blueprint, flash, redirect, url_for, jsonify, current_app, session
from VoteFlow.models import School, Poll, Student, Nominee
from VoteFlow.election.forms import StudentLogin
from flask_login import login_required, current_user
from VoteFlow import db
from functools import wraps
import pprint

# Register this Page as a Blueprint
election = Blueprint('election', __name__)

# Simple Decorator to check for active polls only
# def activepollrequired(func):
# 	@wraps(func)
# 	def func_wrapper(school_abbr, poll_id):
# 		poll = Poll.query.filter_by(host=school_abbr, id=poll_id).first()
# 		if(poll.status == 'Active'):
# 			return func(school_abbr, poll_id)
# 		else:
# 			flash(f'The Poll ({poll.poll_name}) is currently not Active.', 'danger')
# 			return redirect(url_for('polls.pollscreen', school_abbr=school_abbr))
# 	return func_wrapper

# def studentloginrequired(func):
# 	@wraps(func)
# 	def func_wrapper(school_abbr, poll_id, s_id):
# 		isloggedin = session.get('logged_in')
# 		if(not isloggedin):
# 			flash(f'This Page is Password Protected! Please Login to Continue!', 'danger')
# 			return redirect(url_for('election.studentlogin', school_abbr=school_abbr, poll_id=poll_id))
# 		else:
# 			return func(school_abbr, poll_id, s_id=s_id)
# 	return func_wrapper
	
def prepareNominees(nominees, posts):
	displayednominees = []
	for post in posts:
		xnominees = []
		for nominee in nominees:
			if(nominee['post'] == post):
				xnominees.append(nominee)
		displayednominees.append({
			'post': post,
			'nominees': xnominees
		})
	return displayednominees

def castVote(posts, s_id):
	for post in posts:
		nominee_id = request.form[post]
		nominee = Nominee.query.filter_by(id=nominee_id).first()
		nominee.votes += 1
		current_student = Student.query.filter_by(id=s_id).first()
		current_student.voted = True
		db.session.commit()

@election.route('/')
@login_required
# @activepollrequired
def splashscreen(school_abbr, poll_id):
	poll = Poll.query.filter_by(host=school_abbr, id=poll_id).first()
	school = School.query.filter_by(school_abbr=school_abbr).first()
	return render_template('election/splashscreen.html', title="Election", school=school, poll=poll)

@election.route('/studentlogin', methods=['GET', 'POST'])
@login_required
# @activepollrequired
def studentlogin(school_abbr, poll_id):
	poll = Poll.query.filter_by(host=school_abbr, id=poll_id).first()
	school = School.query.filter_by(school_abbr=school_abbr).first()
	form = StudentLogin()
	if(form.validate_on_submit()):
		username = request.form['username'].upper()
		password = request.form['password'].upper()
		student = Student.query.filter_by(school=school.school_abbr, poll=poll.id, username=username, password=password).first()
		if(student):
			if(student.voted == False):
				#Login Successful
				# session['logged_in'] = True
				return redirect(url_for('election.votingpage', school_abbr=school_abbr, poll_id=poll_id, s_id=student.id))
			else:
				flash('A Single User cannot Vote more than Once!', 'danger')
				return redirect(url_for('election.studentlogin', school_abbr=school_abbr, poll_id=poll_id))
		else:
			flash('Either the Username or the Password is Incorrect. Please check Credentials. Do not ignore the Case', 'danger')
			return redirect(url_for('election.studentlogin', school_abbr=school_abbr, poll_id=poll_id))
	return render_template('election/login.html', title="Election", school=school, poll=poll, form=form, poll_name=poll.poll_name)

@election.route('/studentlogout/<s_id>')
@login_required
# @studentloginrequired
# @activepollrequired
def studentlogout(school_abbr, poll_id, s_id):
	# session['logged_in'] = False
	return redirect(url_for('election.studentlogin', school_abbr=school_abbr, poll_id=poll_id))


@election.route('/votingpage/<s_id>', methods=['GET', 'POST'])
@login_required
# @studentloginrequired
# @activepollrequired
def votingpage(school_abbr, poll_id, s_id):
	# if(request.user_agent.browser == 'chrome'):
	# 	return redirect(url_for('main.nochrome'))
	poll = Poll.query.filter_by(host=school_abbr, id=poll_id).first()
	school = School.query.filter_by(school_abbr=school_abbr).first()
	current_student = Student.query.filter_by(school=school.school_abbr, poll=poll.id, id=s_id).first()
	electype = poll.poll_type
	nominees = Nominee.query.filter_by(school=school_abbr, poll=poll_id).all()
	applicable_nominees = []

	if(request.method == 'POST'):
		if(electype == 'A2A'):
			posts = {x.post[1:-1] for x in nominees}
			castVote(posts, s_id)
		if(electype == 'G-I2I'):
			posts = {x.post.split('-')[1][1:-1] for x in nominees}
			castVote(posts, s_id)
		if(electype == 'H-I2I'):
			posts = {x.post.split('-')[1][1:-1] for x in nominees}
			castVote(posts, s_id)
		elif(electype == 'GH-I2I'):
			posts = {x.post.split('-')[2][1:-1] for x in nominees}
			castVote(posts, s_id)
		return redirect(url_for('election.studentlogout', school_abbr=school_abbr, poll_id=poll_id, s_id=s_id))
	
	
	if(electype == 'A2A'):
		applicable_nominees = []
		for nominee in nominees:
			post = nominee.post
			applicable_nominees.append({
				'post': post,
				'nominee': nominee
			})
		posts = {x['post'] for x in applicable_nominees}
		displayednominees = prepareNominees(applicable_nominees, posts)
		return render_template('election/voting.html', title="Election", school=school, poll=poll, student=current_student, nominees=displayednominees, posts=posts)
		
	elif(electype == 'H-I2I'):
		applicable_nominees = []
		for nominee in nominees:
			formattedpost = nominee.post
			splice = formattedpost.split('-')
			house = splice[0]
			post = splice[1]
			if(house == f"[{current_student.house.upper()}]" or house == '[ANY]'):
				applicable_nominees.append({
					'post': post,
					'nominee': nominee
				})
		posts = {x['post'] for x in applicable_nominees}
		displayednominees = prepareNominees(applicable_nominees, posts)

		return render_template('election/voting.html', title="Election", school=school, poll=poll, student=current_student, nominees=displayednominees, posts=posts)

	elif(electype == 'G-I2I'):
		applicable_nominees = []
		for nominee in nominees:
			formattedpost = nominee.post
			splice = formattedpost.split('-')
			gender = splice[0]
			post = splice[1]
			if(gender == f"[{current_student.gender.upper()}]" or gender == '[ANY]'):
				applicable_nominees.append({
					'post': post,
					'nominee': nominee
				})

		posts = {x['post'] for x in applicable_nominees}
		displayednominees = prepareNominees(applicable_nominees, posts)

		return render_template('election/voting.html', title="Election", school=school, poll=poll, student=current_student, nominees=displayednominees, posts=posts)

	elif(electype == 'GH-I2I'):
		applicable_nominees = []
		for nominee in nominees:
			formattedpost = nominee.post
			splice = formattedpost.split('-')
			house = splice[0]
			gender = splice[1]
			post = splice[2]
			if( ((house == f"[{current_student.house.upper()}]" or house == '[ANY]') and (gender == f"[{current_student.gender.upper()}]" or gender == '[ANY]'))):
				applicable_nominees.append({
					'post': post,
					'nominee': nominee
				})
		posts = {x['post'] for x in applicable_nominees}
		displayednominees = prepareNominees(applicable_nominees, posts)
				
		return render_template('election/voting.html', title="Election", school=school, poll=poll, student=current_student, nominees=displayednominees, posts=posts)

@election.route('/getnomineedata/<id>')
def getnomineedata(school_abbr, poll_id, id):
	nominee = Nominee.query.filter_by(id=id).first()
	url = url_for('static', filename=f'DataStore/{school_abbr}/{poll_id}/' ) + nominee.logo
	print(url)
	return jsonify({'logo_url': url, 'slogan': nominee.slogan})