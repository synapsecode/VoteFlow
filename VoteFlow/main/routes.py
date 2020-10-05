#imports
from flask import render_template, request, Blueprint
# from VoteFlow.models import SchoolUser, Poll
from VoteFlow import db

#Register this Page as a Blueprint
main = Blueprint('main', __name__)

#All Routes
@main.route('/')
def splashscreen():
	return render_template('splashscreen.html', title="VoteFlow")

@main.route('/about')
def about():
	return "VOTEFLOW ABOUT PAGE"

@main.route('/nochrome')
def nochrome():
	return render_template('nochrome.html')