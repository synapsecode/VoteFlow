import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
	SECRET_KEY = '2F5F6CE5AE30B54AA5D7CED1BA566982BAB34BA2814A51CE1865D2C2D8815CD4'
	SQLALCHEMY_DATABASE_URI = 'sqlite:///db.sqlite'
	SQLALCHEMY_TRACK_MODIFICATIONS = False
	UPLOAD_FOLDER = f"{os.getcwd()}\\VoteFlow\\static\\DataStore\\"