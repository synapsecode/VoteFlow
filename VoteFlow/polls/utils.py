import numpy as np
import pandas as pd
from VoteFlow.models import Student
import time
from cloudinary.uploader import upload, destroy
from cloudinary.utils import cloudinary_url

def extract_excel_data(fileobject):
	df = pd.read_excel(fileobject, sheet_name='Sheet1')
	headers = [x for x in df]  # Get all the Headers of the Excel File
	# Convert the DataFrame to a python Dictionary
	df = df.to_dict(orient='list')
	data = []  # This list stores all the Student Objects
	# Gets the total number of columns in the Excel Sheet
	num_rows = len(df['student_name'])
	print(num_rows)

	# Student Dictionary Creation
	for i in range(num_rows):
		print(i)
		data_object = {}
		for header in headers:
			value = df[header][i]
			data_object[header] = value if not (
				value is np.nan or value != value) else ""
		data.append(data_object)
	return data

def createUsername(fullname, grade, section):
	subnames = fullname.strip().split(" ")
	print(subnames)
	firstname = subnames[0]
	username = ""
	# CHECK FOR SINGLE LETTER FIRST NAME
	if(len(firstname) > 2):
		username = "{0}{1}{2}".format(firstname, grade, section)
	else:
		username = "{0}{1}{2}".format(subnames[1], grade, section)
	return username

#Check For Duplocate usernames and report them.
def flagDuplicateUsernames(data):
	# CODE TO GET INDEX OF DUPLICATE NAMES
	def list_duplicates_of(seq, item):
		start_at = -1
		locs = []
		while True:
			try:
				loc = seq.index(item, start_at+1)
			except ValueError:
				break
			else:
				locs.append(loc)
				start_at = loc
		return locs

	# GET INDEX OF DUPLICATES
	usernames = [data[x]['username'] for x in range(len(data))]
	all_indexes = [list_duplicates_of(usernames, u) for u in usernames]

	# REMOVING DUPLICATE INDEXES
	duplicateIndexes = []
	for d in all_indexes:
		if(len(d) > 1):
			if d not in duplicateIndexes:
				duplicateIndexes.append(d)
	# GET DUPLICATE ITEMS FROM INDEXES
	duplicatedObjects = []
	for e in duplicateIndexes:
		for index in e:
			duplicatedObjects.append(data[index])

	#SEND BACK DB OBJECTS
	student_objects = []
	for i in range(len(duplicatedObjects)):
		student = Student.query.filter_by(id=int(duplicatedObjects[i]['id']), roll_no=duplicatedObjects[i]['roll_no']).first()
		student_objects.append(student)
	return student_objects

def upload_file_to_cloud(filename, filetype=None):
	try:
		start = time.time()
		# Initialize Variables
		objectURI = ""
		if(filetype != None):
			uploaded_object = upload(filename,
									 notification_url="http://localhost",
									 api_key="567258933887428",
									 resource_type=str(filetype),
									 api_secret="4fbRuagJOs6v8qEeUM98nCZlylE",
									 cloud_name="krustel-synapse"
									 )
			objectURI = uploaded_object['secure_url']
		else:
			uploaded_object = upload(filename,
									 notification_url="http://localhost",
									 api_key="567258933887428",
									 api_secret="4fbRuagJOs6v8qEeUM98nCZlylE",
									 cloud_name="krustel-synapse"
									 )
			objectURI = uploaded_object['secure_url']

		end = time.time()
		print(f"TOOK {int(end-start)} seconds to finish")
		return({
			"STATUS": "OK",
			"URI": str(objectURI),
		})
	except Exception as e:
		print(e)
		return({
			"STATUS": "ERR",
			"ERRCODE": str(e)
		})

def uploadImageToCloud():
	try:
		#Upload Logo to Cloud and assign it to individual user:
		import glob
		for filepath in glob.iglob(f'{path}/TempLogos/*.jpg'):
			img_name = os.path.basename(filepath).replace('_', ' ')
			print(img_name)
			nominee = Nominee.query.filter_by(full_name=img_name.split(".")[0], poll=poll_id, school=school_abbr).first()
			#Upload Logo
			with open(file=filepath, mode='r') as f:
				uploaded_thumbnail = upload_file_to_cloud(filepath)
				if(uploaded_thumbnail['STATUS'] == 'OK'):
					nominee.logo = uploaded_thumbnail['URI']
					db.session.commit()
				else:
					print(uploaded_thumbnail)
		flash('Successfully Uploaded all nominees!', 'success')
	except Exception as e:
		print(e)
		flash('Error Occured!', 'danger')

	#Delete Everything im TempLogos
	import shutil
	shutil.rmtree(f'{path}/TempLogos')
	os.mkdir(f'{path}/TempLogos')