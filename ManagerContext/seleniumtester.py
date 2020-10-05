from selenium import webdriver
from selenium.webdriver.support.select import Select
from selenium.webdriver.common.keys import Keys
from VoteFlow import create_app, db
from VoteFlow.models import Poll, Student
from random import randint

browser = webdriver.Chrome('C:\\Users\\manas\\Downloads\\chromedriver')

def login():
	#Launch Page
	browser.get('localhost/login')
	#Choose School
	schoolselector = Select(browser.find_element_by_id("schoolselector"))
	schoolselector.select_by_value('spes')
	#Enter School Username
	usernameBox = browser.find_element_by_id('username')
	usernameBox.send_keys('stpaulsenglishschool')
	#Enter School Password
	usernameBox = browser.find_element_by_id('password')
	usernameBox.send_keys('spes123')
	#Sumbit
	submitButton = browser.find_element_by_id('submit')
	submitButton.click()

	print("Login Completed Successfully!")

def createPoll():
	#Launch Page
	browser.get('localhost/spes/polls')
	#Click on New Poll Button
	newpollbtn = browser.find_element_by_id('newpoll')
	newpollbtn.click()
	#Enter Poll Name
	usernameBox = browser.find_element_by_id('poll_name')
	usernameBox.send_keys('Trial Elections')
	#Choose Election Type
	schoolselector = Select(browser.find_element_by_id("electype"))
	schoolselector.select_by_value('GH-I2I')

	houses = "[RUBY]\n[TOPAZ]\n[SAPPHIRE]\n[EMERALD]"
	positions = "[HOUSE]-[GENDER]-[HOUSE VICE CAPTAIN]\n[ANY]-[GENDER]-[SCHOOL VICE CAPTAIN]\n[ANY]-[GENDER]-[SPORTS VICE CAPTAIN]\n[ANY]-[GENDER]-[CULTURAL VICE CAPTAIN]"
	
	#Enter Houses
	houseBox = browser.find_element_by_id('houses')
	houseBox.send_keys(houses)
	#Enter Positions
	positionsBox = browser.find_element_by_id('positions')
	positionsBox.send_keys(positions)
	#Enter Year
	yearBox = browser.find_element_by_id('year')
	yearBox.send_keys('2019')
	#Submit
	submitButton = browser.find_element_by_id('newpoll')
	submitButton.click()

	print("Poll Creation Completed Successfully!")

def clickpoll():
	poll = None
	app = create_app()
	with app.app_context():
		poll = Poll.query.filter_by(host='spes', poll_name='Trial Elections 2').first()
	#Launch Page
	browser.get(f'localhost/spes/polls/{poll.id}')
	#Click on Student Upload
	browser.get(f'localhost/spes/polls/{poll.id}/addstudents')
	studentfile = browser.find_element_by_id('students')
	studentfile.send_keys('C:\\Users\\manas\\OneDrive\\Desktop\\ELECDATA\\studentMaster.xls')
	submitButton = browser.find_element_by_id('submit')
	submitButton.click()
	#Click on Nominee Upload
	browser.get(f'localhost/spes/polls/{poll.id}/addnominees')
	nomineesfile = browser.find_element_by_id('nominees')
	nomineesfile.send_keys('C:\\Users\\manas\\OneDrive\\Desktop\\ELECDATA\\nomineesMaster.xls')
	logofile = browser.find_element_by_id('nominees_logo')
	logofile.send_keys('C:\\Users\\manas\\OneDrive\\Desktop\\ELECDATA\\Election Logo Master.zip')
	submitButton = browser.find_element_by_id('submit')
	submitButton.click()
	#Activate Elections
	browser.get(f'localhost/spes/polls/{poll.id}/startelection')
	submitButton = browser.find_element_by_id('elecstart')
	submitButton.click()

def student_login():
	#Get number of students
	poll = None
	students = []
	app = create_app()
	with app.app_context():
		poll = Poll.query.filter_by(host='spes', poll_name='High School Elections').first()
		students = Student.query.filter_by(poll=poll.id).all()
	for student in students:
		browser.get(f'localhost/spes/election/{poll.id}/votingpage/{student.id}')
		#SPVC
		sportsvc = Select(browser.find_element_by_id("SPORTS VICE CAPTAIN"))
		sportsvc.select_by_index(randint(0, len(sportsvc.options) - 1))
		#CVC
		culturalvc = Select(browser.find_element_by_id("CULTURAL VICE CAPTAIN"))
		culturalvc.select_by_index(randint(0, len(culturalvc.options) - 1))
		#SVC
		schoolvc = Select(browser.find_element_by_id("SCHOOL VICE CAPTAIN"))
		schoolvc.select_by_index(randint(0, len(schoolvc.options) - 1))
		#HVC
		housevc = Select(browser.find_element_by_id("HOUSE VICE CAPTAIN"))
		housevc.select_by_index(randint(0, len(housevc.options) - 1))

		#SUBMIT
		submitButton = browser.find_element_by_id('submit')
		submitButton.click()
		


if __name__ == '__main__':
	login()
	createPoll()
	#student_login()
