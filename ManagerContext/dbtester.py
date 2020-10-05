from VoteFlow import create_app, db
from VoteFlow.models import Poll, Student, FlaggedStudent, Nominee
import pprint
app = create_app()
with app.app_context():
	students = Student.query.all()
	flaggedstudents = FlaggedStudent.query.all()
	polls = Poll.query.all()
	nominees = Nominee.query.all()
	[db.session.delete(s) for s in students]
	[db.session.delete(f) for f in flaggedstudents]
	#[db.session.delete(j) for j in polls]
	[db.session.delete(n) for n in nominees]
	# xpoll = polls[0]
	# print(xpoll.poll_name)
	# pos = xpoll.positions
	# pprint.pprint(pos)
	db.session.commit()