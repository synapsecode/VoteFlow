# imports
from flask import render_template, request, Blueprint, flash, redirect, url_for, jsonify, current_app, send_from_directory
from VoteFlow.models import School, Poll, Student, FlaggedStudent, Nominee, Results
from flask_login import login_required, current_user
from VoteFlow import db
from VoteFlow.polls.forms import (
	NewPollForm, CreatePollForm, AddStudentsForm, AddNomineesForm, EditFlaggedUsernameForm)
import io
from .utils import extract_excel_data, createUsername, flagDuplicateUsernames, upload_file_to_cloud
from werkzeug.utils import secure_filename
import pprint
import numpy as np
from functools import wraps
import xlwt 
from xlwt import Workbook 

# Register this Page as a Blueprint
polls = Blueprint('polls', __name__)

def activeandscheduledpollrequired(func):
	@wraps(func)
	def func_wrapper(school_abbr, poll_id):
		poll = Poll.query.filter_by(host=school_abbr, id=poll_id).first()
		if(poll.status != 'Archived'):
			return func(school_abbr, poll_id)
		else:
			flash(f'This Poll has been Archived! The Dashboard cannot be viewed for a Archived Poll', 'danger')
			return redirect(url_for('polls.pollscreen', school_abbr=school_abbr))
	return func_wrapper

def GetPositions(etype, queryData, houseData):
	data = queryData
	houses = houseData
	# Completely Open Elections
	if(etype == 'A2A'):
		return [x for x in data]
	# House Based Elections
	elif(etype == 'H-I2I'):
		positions = []
		for post in data:
			splice = post.split("-")
			house, post = splice[0], splice[1]
			# Check If House value specified
			if(house != "[ANY]"):
				[positions.append(f'{i}-{post}') for i in houses]
			else:
				positions.append(f'[ANY]-{post}')
		return positions
	elif(etype == 'G-I2I'):
		positions = []
		for post in data:
			splice = post.split("-")
			gender, post = splice[0], splice[1]
			if(gender != '[ANY]'):
				[positions.append(f'[{g}]-{post}') for g in ['M', 'F']]
			else:
				positions.append(f'[ANY]-{post}')
		return positions
	elif(etype == 'GH-I2I'):
		positions = []
		for post in data:
			print(f'DATA -> {post}')
			splice = post.split("-")
			house, gender, post = splice[0], splice[1], splice[2]
			if(house != "[ANY]"):
				for i in houses:
					if(gender != "[ANY]"):
						[positions.append(f"{i}-[{g}]-{post}")
						 for g in ['M', 'F']]
					else:
						positions.append(f"{i}-[ANY]-{post}")
			else:
				if(gender != "[ANY]"):
					[positions.append(f"[ANY]-[{g}]-{post}")
					 for g in ['M', 'F']]
				else:
					positions.append(f"[ANY]-[ANY]-{post}")
		return positions


def add_record(nominee, school, poll, gender=None, house=None):
	nominee_objects = []
	electype = poll.poll_type
	if(electype == 'A2A'):
		new_nominee = Nominee(
			school=school.school_abbr,
			poll=poll.id,
			full_name=nominee['student_name'],
			house="",
			gender="",
			post=f"[{nominee['post']}]",
			logo=f"{nominee['student_name'].replace(' ', '_')}.jpg",
			slogan=nominee['slogan'],
			votes=0
		)
		nominee_objects.append(new_nominee)
	elif(electype == 'G-I2I'):
		new_nominee = Nominee(
			school=school.school_abbr,
			poll=poll.id,
			full_name=nominee['student_name'],
			post=f"{gender}-[{nominee['post']}]",
			house="",
			gender=gender[1:-1],
			logo=f"{nominee['student_name'].replace(' ', '_')}.jpg",
			slogan=nominee['slogan'],
			votes=0
		)
		nominee_objects.append(new_nominee)
	elif(electype == 'H-I2I'):
		new_nominee = Nominee(
			school=school.school_abbr,
			poll=poll.id,
			full_name=nominee['student_name'],
			post=f"{house}-[{nominee['post']}]",
			house=house[1:-1],
			gender="",
			logo=f"{nominee['student_name'].replace(' ', '_')}.jpg",
			slogan=nominee['slogan'],
			votes=0
		)
		nominee_objects.append(new_nominee)
	elif(electype == 'GH-I2I'):
		new_nominee = Nominee(
			school=school.school_abbr,
			poll=poll.id,
			full_name=nominee['student_name'],
			post=f"{house}-{gender}-[{nominee['post']}]",
			house=house[1:-1],
			gender=gender[1:-1],
			logo=f"{nominee['student_name'].replace(' ', '_')}.jpg",
			slogan=nominee['slogan'],
			votes=0
		)
		nominee_objects.append(new_nominee)
	return nominee_objects

def getPollLink(poll_id):
	poll = Poll.query.filter_by(id=poll_id).first()
	return f"{request.host_url[:-1]}{url_for('election.splashscreen', school_abbr=poll.host, poll_id=poll.id)}"


# All Routes


@polls.route('/', methods=['GET', 'POST'])
@login_required
def pollscreen(school_abbr):
	if(current_user.school_abbr == school_abbr):
		form = NewPollForm()
		if(form.is_submitted()):
			return redirect(url_for('polls.create_poll', school_abbr=current_user.school_abbr))

		school = School.query.filter_by(school_abbr=school_abbr).first()
		# Getting Polls From Database
		activepolls = Poll.query.filter_by(
			host=school.school_abbr, status="Active").all()
		scheduledpolls = Poll.query.filter_by(
			host=school.school_abbr, status="Scheduled").all()
		archivedpolls = Poll.query.filter_by(
			host=school.school_abbr, status="Archived").all()
		return render_template('pollscreen.html', title="Dashboard", school_name=school.schoolname, accent_color=school.accent_color,
							   activepolls=activepolls, scheduledpolls=scheduledpolls, archivedpolls=archivedpolls, form=form, linker=getPollLink)
	else:
		flash("You cannot access another user's dashboard!", 'danger')
		return redirect(url_for('polls.pollscreen', school_abbr=current_user.school_abbr))


@polls.route('/createpoll', methods=['GET', 'POST'])
@login_required
def create_poll(school_abbr):
	if(current_user.school_abbr == school_abbr):
		form = CreatePollForm()
		if(form.validate_on_submit()):
			# Get Data
			poll_name, poll_type, houses = request.form[
				'poll_name'], request.form['poll_type'], request.form['houses']
			positions, year = request.form['positions'], request.form['year']
			# Process Data
			positions_splitted = [x.rstrip() for x in positions.split('\n')]
			houses_splitted = [x.rstrip() for x in houses.split('\n')]
			positions = GetPositions(
				poll_type, positions_splitted, houses_splitted)
			# Add Data to Database
			new_poll = Poll(
				host=current_user.school_abbr,
				poll_name=poll_name,
				poll_type=poll_type,
				houses=houses_splitted,
				positions=positions,
				year=year,
				status='Scheduled'
			)
			db.session.add(new_poll)
			db.session.commit()

			#Generate Logo Directory
			import os
			path = f"{os.getcwd()}\\VoteFlow{url_for('static', filename='DataStore')}"
			poll = Poll.query.filter_by(poll_name=poll_name, host=current_user.school_abbr).first()
			os.mkdir(f'{path}/{school_abbr}/{poll.id}')

			flash(f"Successfully Created Poll '{poll_name}'", 'success')
			return redirect(url_for('polls.pollscreen', school_abbr=current_user.school_abbr))
		return render_template('createpoll.html', title="Create Poll", form=form, nocontainer=True)
	else:
		flash("You cannot access another user's page!")


@polls.route('/<poll_id>', methods=['GET', 'POST'])
@login_required
@activeandscheduledpollrequired
def dashboard_home(school_abbr, poll_id):
	poll = Poll.query.filter_by(host=school_abbr, id=poll_id).first()
	school = School.query.filter_by(school_abbr=school_abbr).first()
	if(current_user.school_abbr == school_abbr):
		if(poll.status == 'Active'):
			if(request.method == 'POST'):
				return redirect(url_for('polls.startelection', school_abbr=school.school_abbr, poll_id=poll.id))
			link = getPollLink(poll.id)
			return render_template('polldashboard/home.html', title=poll.poll_name, school=school, poll=poll, status="Active", link=link)
		return render_template('polldashboard/home.html', title=poll.poll_name, school=school, poll=poll)
	else:
		flash("You cannot access another user's page!", 'danger')
		return redirect(url_for('polls.dashboard_home', school_abbr=current_user.school_abbr, poll_id=poll_id))


@polls.route('/<poll_id>/settings', methods=['GET', 'POST'])
@login_required
@activeandscheduledpollrequired
def general_settings(school_abbr, poll_id):
	poll = Poll.query.filter_by(host=school_abbr, id=poll_id).first()
	school = School.query.filter_by(school_abbr=school_abbr).first()
	if(current_user.school_abbr == school_abbr):
		return render_template('polldashboard/settings.html', title=poll.poll_name, school=school, poll=poll)
	else:
		flash("You cannot access another user's page!", 'danger')
		return redirect(url_for('polls.general_settings', school_abbr=current_user.school_abbr, poll_id=poll_id))


@polls.route('/<poll_id>/addstudents', methods=['GET', 'POST'])
@login_required
@activeandscheduledpollrequired
def add_students(school_abbr, poll_id):
	poll = Poll.query.filter_by(host=school_abbr, id=poll_id).first()
	school = School.query.filter_by(school_abbr=school_abbr).first()
	form = AddStudentsForm()
	loaded_students = Student.query.filter_by(
		school=school.school_abbr, poll=poll.id).all()
	flagged = []
	if(form.validate_on_submit()):
		studentMetadata = []
		studentDataFile = request.files['students']
		studentsBytes = io.BytesIO(studentDataFile.read())
		students = extract_excel_data(studentsBytes)

		# Add to Database
		created_students = []
		for student in students:
			new_student = Student(
				school=school.school_abbr,
				poll=poll.id,
				full_name=student['student_name'].strip(),
				grade=student['grade'],
				section=student['section'],
				roll_no=student['roll_no'],
				gender=student['gender'],
				house=student['house'],
				voted=False,
				username=createUsername(
					student['student_name'], student['grade'], student['section']),
				password=student['password']
			)
			created_students.append(new_student)
		# Adds everything to the session
		db.session.bulk_save_objects(created_students)
		db.session.commit()  # Commits to database

		# Check For Duplicates

		# Generate Metadata for Every Student
		for student in Student.query.filter_by(school=school.school_abbr, poll=poll.id).distinct():
			studentMetadata.append({
				'id': student.id,
				"full_name": student.full_name,
				"username": student.username,
				"roll_no": student.roll_no,
			})

		# Initiate Flagging Procedure {DuplicateUsernames are not allowed and will be flagged}
		flagged = flagDuplicateUsernames(studentMetadata)

		# Add it to the Flagged DB
		flagged_students = []
		for student in flagged:
			flagged_student = FlaggedStudent(
				student_id=student.id, poll_id=poll.id, school_id=school.id)
			flagged_students.append(flagged_student)
		db.session.bulk_save_objects(flagged_students)
		db.session.commit()

		flash("Successfully Added Students!", 'success')
		return render_template('polldashboard/addstudents.html', title=poll.poll_name, school=school, poll=poll, form=form, flagged=flagged, host=request.host_url[:-1])

	if(current_user.school_abbr == school_abbr):
		flagged = FlaggedStudent.query.filter_by(
			poll_id=poll.id, school_id=school.id).all()
		if(loaded_students):
			return render_template('polldashboard/addstudents.html', title=poll.poll_name, school=school, poll=poll, form=form, flagged=flagged)
		else:
			return render_template('polldashboard/addstudents.html', title=poll.poll_name, school=school, poll=poll, form=form, loaded=True)
	else:
		flash("You cannot access another user's page!", 'danger')
		return redirect(url_for('polls.add_students', school_abbr=current_user.school_abbr, poll_id=poll_id))


@polls.route('/<poll_id>/editflaggedstudents', methods=['GET', 'POST'])
@login_required
@activeandscheduledpollrequired
def edit_flagged_students(school_abbr, poll_id):
	school = School.query.filter_by(school_abbr=school_abbr).first()
	poll = Poll.query.filter_by(id=poll_id).first()
	flagged = FlaggedStudent.query.filter_by(
		school_id=school.id, poll_id=poll_id).all()
	form = EditFlaggedUsernameForm()
	if(request.method == "GET"):
		flagged_students = []
		for f in flagged:
			student = Student.query.filter_by(id=f.student_id).first()
			flagged_students.append(student)
		return render_template('polldashboard/editflaggedstudents.html', title="Edit Flagged Students", flagged=flagged_students, school=school, poll=poll, form=form)
	elif(request.method == "POST"):
		n = len(flagged)
		usernames = [request.form[f'd{i}'] for i in range(n)]
		students = [Student.query.filter_by(
			id=f.student_id).first() for f in flagged]
		print(usernames)
		for record, username in zip(students, usernames):
			print(f"RECORD {record.username} -> {username}")
			record.username = username
			db.session.add(record)
			# Remove the Flagged Student
			db.session.delete(FlaggedStudent.query.filter_by(
				school_id=school.id, poll_id=poll.id, student_id=record.id).first())
		db.session.commit()
		flash('Successfully Edited All Usernames!', 'success')
		return redirect(url_for('polls.edit_flagged_students', school_abbr=school.school_abbr, poll_id=poll_id))


@polls.route('/<poll_id>/addnominees', methods=['GET', 'POST'])
@login_required
@activeandscheduledpollrequired
def add_nominees(school_abbr, poll_id):
	poll = Poll.query.filter_by(host=school_abbr, id=poll_id).first()
	school = School.query.filter_by(school_abbr=school_abbr).first()
	form = AddNomineesForm()
	loaded_nominees = Nominee.query.filter_by(school=school.school_abbr, poll=poll.id).all()
	if(form.validate_on_submit()):
		nomineesDataFile = request.files['nominees']
		logoBundle = request.files['nominees_logo']
		nomineesBytes = io.BytesIO(nomineesDataFile.read())
		nominees = extract_excel_data(nomineesBytes)

		#Save the Logo Bundle
		import os
		filename = f"{school_abbr}-{poll.id}-nominees.{(logoBundle.filename).split('.')[1]}"
		logoBundle.save(os.path.join(current_app.config['UPLOAD_FOLDER'], secure_filename(filename)))

		# Get the Election Type
		electype = poll.poll_type
		positions = poll.positions

		if(electype == 'A2A'):
			for post in positions:
				for nominee in nominees:
					if(post == f"[{nominee['post']}]"):
						db.session.bulk_save_objects(
							add_record(nominee, school, poll))
						db.session.commit()
			print(len(Nominee.query.filter_by(school=school_abbr, poll=poll_id).all()))

		elif(electype == 'G-I2I'):
			print(nominees)
			for post in positions:
				for nominee in nominees:
					if(post.split('-')[1] == f"[{nominee['post']}]"):
						if(post.split('-')[0] == f"[{nominee['gender']}]"):
							db.session.bulk_save_objects(add_record(
								nominee, school, poll, gender=post.split("-")[0]))
							db.session.commit()
						elif(post.split('-')[0] == '[ANY]'):
							db.session.bulk_save_objects(add_record(
								nominee, school, poll, gender='[ANY]'))
							db.session.commit()
		elif(electype == 'H-I2I'):
			for post in positions:
				for nominee in nominees:
					if(post.split('-')[1] == f"[{nominee['post']}]"):
						if(post.split('-')[0] == f"[{nominee['house']}]"):
							db.session.bulk_save_objects(add_record(
								nominee, school, poll, house=post.split("-")[0]))
							db.session.commit()
						elif(post.split('-')[0] == '[ANY]'):
							db.session.bulk_save_objects(add_record(
								nominee, school, poll, house='[ANY]'))
							db.session.commit()
		elif(electype == 'GH-I2I'):
			for post in positions:
				for nominee in nominees:
					if(post.split('-')[2] == f"[{nominee['post']}]"):
						#House
						if(post.split('-')[0] == f"[{nominee['house']}]"):
							#Gender
							if(post.split('-')[1] == f"[{nominee['gender']}]"):
								db.session.bulk_save_objects(add_record(
									nominee, school, poll, house=post.split('-')[0], gender=post.split('-')[1]))
								db.session.commit()
							elif(post.split('-')[1] == '[ANY]'):
								db.session.bulk_save_objects(add_record(
									nominee, school, poll, house=post.split('-')[0], gender='[ANY]'))
								db.session.commit()
						#House
						elif(post.split('-')[0] == '[ANY]'):
							#Gender
							if(post.split('-')[1] == f"[{nominee['gender']}]"):
								db.session.bulk_save_objects(add_record(
									nominee, school, poll, house='[ANY]', gender=post.split('-')[1]))
								db.session.commit()
							elif(post.split('-')[1] == '[ANY]'):
								db.session.bulk_save_objects(add_record(
									nominee, school, poll, house='[ANY]', gender='[ANY]'))
								db.session.commit()

		#Extract the Zip File	
		import zipfile
		import os

		path = f"{os.getcwd()}\\VoteFlow{url_for('static', filename='DataStore')}"
		print(path)
		with zipfile.ZipFile(f"{path}/{filename}","r") as zip_ref:
			zip_ref.extractall(f"{path}/{school_abbr}/{poll_id}/")

		#Add Files to Name
		import glob
		for filepath in glob.iglob(f'{path}/{school_abbr}/{poll_id}/*.jpg'):
			img_name = os.path.basename(filepath).replace('_', ' ')
			print(img_name)
			nominee = Nominee.query.filter_by(full_name=img_name.split(".")[0], poll=poll_id, school=school_abbr).first()
			nominee.logo = os.path.basename(filepath)
			db.session.commit()
		

		#Remove the Zip File
		os.remove(f"{path}/{filename}")
		flash('Successfully Uploaded all nominees!', 'success')
		return render_template('polldashboard/addnominees.html', title=poll.poll_name, school=school, poll=poll, form=form, loaded=True)
	
	if(current_user.school_abbr == school_abbr):
		if(loaded_nominees):
			return render_template('polldashboard/addnominees.html', title=poll.poll_name, school=school, poll=poll, form=form, loaded=True)
		else:
			return render_template('polldashboard/addnominees.html', title=poll.poll_name, school=school, poll=poll, form=form)
	else:
		flash("You cannot access another user's page!", 'danger')
		return redirect(url_for('polls.add_nominees', school_abbr=current_user.school_abbr, poll_id=poll_id))

# new_nominee = Nominee(
# 	school=school.abbr,
# 	poll=poll.id,
# 	full_name=nominee['student_name'],
# 	post=f"{p.split('-')[0]}-{gender}-{post}",
# 	house=f"[{nominee.house}]",
# 	gender=gender,
# 	logo=f"{nominee['name'].replace(' ', '_')}.jpg",
# 	slogan=nominee['slogan'],
# 	votes=0
# )
# db.session.add(new_nominee)
# db.session.commit()


@polls.route('/<poll_id>/startelection', methods=['GET', 'POST'])
@login_required
@activeandscheduledpollrequired
def startelection(school_abbr, poll_id):
	poll = Poll.query.filter_by(host=school_abbr, id=poll_id).first()
	school = School.query.filter_by(school_abbr=school_abbr).first()
	link = getPollLink(poll.id)
	if(current_user.school_abbr == school_abbr):
		if(request.method == 'POST'):
			#Start Election Code
			poll.status = "Active"
			db.session.commit()
			flash(f'Poll ({poll.poll_name}) has been officially started and is currently active!', 'success')
			link = getPollLink(poll.id)
			return render_template('polldashboard/startelection.html', title=poll.poll_name, school=school, poll=poll, started=True, link=link)
		
		if(poll.status == 'Active'):
			return render_template('polldashboard/startelection.html', title=poll.poll_name, school=school, poll=poll, started=True, link=link)
		
		return render_template('polldashboard/startelection.html', title=poll.poll_name, school=school, poll=poll)
	else:
		flash("You cannot access another user's page!", 'danger')
		return redirect(url_for('polls.startelection', school_abbr=current_user.school_abbr, poll_id=poll_id))


@polls.route('/<poll_id>/deletepoll', methods=['GET', 'POST'])
@login_required
@activeandscheduledpollrequired
def deletepoll(school_abbr, poll_id):
	poll = Poll.query.filter_by(host=school_abbr, id=poll_id).first()
	school = School.query.filter_by(school_abbr=school_abbr).first()
	if(current_user.school_abbr == school_abbr):
		if(request.method == 'POST'):
			#Delete Students
			[db.session.delete(x) for x in Student.query.filter_by(poll=poll_id).all()]
			#Delete Nominees
			[db.session.delete(y) for y in Nominee.query.filter_by(poll=poll_id).all()]
			#Delete Poll
			db.session.delete(poll)
			db.session.commit()
			flash(f'Successfully Deleted Poll ({poll.poll_name})', 'success')
			return redirect(url_for('polls.pollscreen', school_abbr=current_user.school_abbr))
		return render_template('polldashboard/deletepoll.html', title=poll.poll_name, school=school, poll=poll)
	else:
		flash("You cannot access another user's page!", 'danger')
		return redirect(url_for('polls.deletepoll', school_abbr=current_user.school_abbr, poll_id=poll_id))

@polls.route('/<poll_id>/results', methods=['GET', 'POST'])
@login_required
@activeandscheduledpollrequired
def results(school_abbr, poll_id):
	poll = Poll.query.filter_by(host=school_abbr, id=poll_id).first()
	school = School.query.filter_by(school_abbr=school_abbr).first()
	if(request.method == 'POST'):
		poll.status = "Archived"
		all_results = []
		for post in poll.positions:
			nominees = Nominee.query.filter_by(school=school_abbr, poll=poll_id, post=post).all()
			votes = [x.votes for x in nominees]
			winner = nominees[votes.index(max(votes))]
			all_results.append(Results(school=school_abbr, poll=poll_id, full_name=winner.full_name, post=post, votes=winner.votes))
		db.session.bulk_save_objects(all_results)
		db.session.commit()
		for winner in Results.query.filter_by(school=school_abbr, poll=poll_id):
			print(f"{winner.post} -> {winner.full_name}: {winner.votes}")
			
		#TODO: DELETE NOMINEES
		#TODO: DELETE STUDENTS
		return redirect(url_for('polls.resultspage', school_abbr=current_user.school_abbr, poll_id=poll_id))

	if(current_user.school_abbr == school_abbr):
		return render_template('polldashboard/results.html', title=poll.poll_name, school=school, poll=poll)
	else:
		flash("You cannot access another user's page!", 'danger')
		return redirect(url_for('polls.results', school_abbr=current_user.school_abbr, poll_id=poll_id))

@polls.route('/<poll_id>/resultspage', methods=['GET', 'POST'])
@login_required
def resultspage(school_abbr, poll_id):
	poll = Poll.query.filter_by(host=school_abbr, id=poll_id).first()
	school = School.query.filter_by(school_abbr=school_abbr).first()
	if(poll.status == "Archived"):
		results = Results.query.filter_by(school=school_abbr, poll=poll_id).all()
		stats = (len(Student.query.filter_by(voted=True, school=school_abbr, poll=poll.id).all()),len(Student.query.filter_by(school=school_abbr, poll=poll.id).all()))
		print(results)
		return render_template('polldashboard/resultsdisplay.html', title="Results", res=results, polltype=poll.poll_type, stats=stats, school=school_abbr, poll_id=poll_id)
	else:
		flash("Cannot Declare Results for an Active Poll", 'danger')
		return redirect(url_for('polls.dashboard_home', school_abbr=current_user.school_abbr, poll_id=poll_id))	
	return render_template('polldashboard/resultsdisplay.html', title="Results")

@polls.route('/<poll_id>/updatedata', methods=['GET', 'POST'])
@login_required
@activeandscheduledpollrequired
def updatedata(school_abbr, poll_id):
	students = Student.query.filter_by(school=school_abbr, poll=poll_id).all()
	poll = Poll.query.filter_by(id=poll_id).first()
	houses = ["RUBY", "TOPAZ", "EMERALD", "SAPPHIRE"]
	if(request.method == 'POST'):
		gender = request.form['gender']
		house = None
		if(poll.poll_type == 'GH-I2I'):
			house = request.form['house']
			if(gender.split('-')[0] == house.split('-')[0]):
				s_id = gender.split('-')[0]
				student = Student.query.filter_by(id=s_id).first()
				student.house = house.split('-')[1]
				student.gender = gender.split('-')[1]
				db.session.commit()
				flash(f"Student ('{student.full_name}') updated successfully", "success")
		else:
			if(gender.split('-')[0]):
				s_id = gender.split('-')[0]
				student = Student.query.filter_by(id=s_id).first()
				#student.house = house.split('-')[1]
				student.gender = gender.split('-')[1]
				db.session.commit()
				flash(f"Student ('{student.full_name}') updated successfully", "success")
	return render_template('polldashboard/updatedata.html', title="Update Data", students=students, houses=houses, p_type=poll.poll_type, p_name=poll.poll_name)

@polls.route('/<poll_id>/downloadelectionsummary', methods=['GET', 'POST'])
@login_required
def downloadelectionsummary(school_abbr, poll_id):
	import os
	nominees = Nominee.query.filter_by(school=school_abbr, poll=poll_id).all()
	poll = Poll.query.filter_by(id=poll_id).first()
	wb = Workbook()
	s = wb.add_sheet('Sheet 1')

	s.write(0, 0, 'nominee_name')
	s.write(0, 1, 'post')
	s.write(0, 2, 'house')
	s.write(0, 3, 'gender')
	s.write(0, 4, 'votes')

	for i, nominee in enumerate(nominees):
		full_name = nominee.full_name
		post = None
		if(poll.poll_type == 'GH-I2I'):
			post = nominee.post.split('-')[2][1:-1]
		elif(poll.poll_type == 'G-I2I'):
			post = nominee.post.split('-')[1][1:-1]
		house = nominee.house
		gender = nominee.gender
		votes = nominee.votes

		s.write(i+1, 0, str(full_name))
		s.write(i+1, 1, str(post))
		if(house == 'ANY'):
			s.write(i+1, 2, "")
		else:
			s.write(i+1, 2, str(house))
		s.write(i+1, 3, str(gender))
		s.write(i+1, 4, int(votes))


	wb.save(os.path.join(current_app.config['UPLOAD_FOLDER'],f'Poll-{poll_id}-Summary.xls'))
	return send_from_directory(os.path.join(current_app.config['UPLOAD_FOLDER']), filename=f'Poll-{poll_id}-Summary.xls')

@polls.route('/<poll_id>/downloadabsenteevoterslist', methods=['GET', 'POST'])
@login_required
def download_absentee_voters_list(school_abbr, poll_id):
	import os
	voters = Student.query.filter_by(school=school_abbr, poll=poll_id, voted=False).all()
	poll = Poll.query.filter_by(id=poll_id).first()
	wb = Workbook()
	s = wb.add_sheet('Sheet 1')

	s.write(0, 0, 'student_name')
	s.write(0, 1, 'grade')
	s.write(0, 2, 'section')

	for i, voter in enumerate(voters):
		full_name = voter.full_name
		grade = voter.grade
		section = voter.section

		s.write(i+1, 0, str(full_name))
		s.write(i+1, 1, str(grade))
		s.write(i+1, 2, str(section))

	wb.save(os.path.join(current_app.config['UPLOAD_FOLDER'],f'Poll-{poll_id}-AbsenteeList.xls'))
	return send_from_directory(os.path.join(current_app.config['UPLOAD_FOLDER']), filename=f'Poll-{poll_id}-AbsenteeList.xls')