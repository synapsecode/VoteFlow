from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from VoteFlow.config import Config

#Initialize Modules
db = SQLAlchemy()
bcrypt = Bcrypt()

#Login Manager for the School
school_login_manager = LoginManager()
school_login_manager.login_view = 'users.school_login'
school_login_manager.login_message_category = 'info'

def create_app(config_class=Config):
	app = Flask(__name__)
	app.config.from_object(Config)
	db.init_app(app) 
	bcrypt.init_app(app)
	school_login_manager.init_app(app)
	from VoteFlow.main.routes import main
	from VoteFlow.users.routes import users
	from VoteFlow.polls.routes import polls
	from VoteFlow.election.routes import election
	app.register_blueprint(main, url_prefix="/")
	app.register_blueprint(users, url_prefix="/")
	app.register_blueprint(polls, url_prefix="/<school_abbr>/polls")
	app.register_blueprint(election, url_prefix="/<school_abbr>/election/<poll_id>")
	return app