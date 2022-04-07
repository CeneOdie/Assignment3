
from unicodedata import category
from flask import Flask, render_template, url_for, redirect, request, session, flash
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import or_, desc, case, join, select
from sqlalchemy.sql import func    
from sqlalchemy.orm import aliased


app = Flask(__name__)
bcrypt = Bcrypt(app)
app.config['SECRET_KEY'] = "AVeryRandomSecretKey"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///assignment3.db'
db = SQLAlchemy(app)


# CREATE TABLES
class User(db.Model):
    __tablename__ = 'User'
    uid = db.Column(db.Integer, primary_key = True)
    firstname = db.Column(db.String(20), nullable = False)
    lastname = db.Column(db.String(20), nullable = False)
    username = db.Column(db.String(20), unique = True, nullable = False)
    email = db.Column(db.String(70), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable = False)

    teacher = db.relationship("Teacher", backref = "teacher", lazy = True)
    student = db.relationship("Student", backref = "studies", lazy = True)

    def __repr__(self):
        return f"User('{self.firstname}' '{self.lastname}', '{self.email}')"

class Course(db.Model):
    __tablename__ = 'Course'
    cid = db.Column(db.Integer, primary_key = True)
    code = db.Column(db.String(6), nullable = False)
    name = db.Column(db.String(30), nullable = False)
    semester = db.Column(db.String(6), nullable=False)
    year = db.Column(db.String(4), nullable = False)

    __table_args__ = (
        db.UniqueConstraint('code', 'semester', 'year'),
    )

    teacher = db.relationship("Teacher", backref = "teaches", lazy = True)
    student = db.relationship("Student", backref = "enrolled", lazy = True)
    assignment = db.relationship("Assignment", backref = "assignmentFor", lazy = True)

    def __repr__(self):
        return f"Course('{self.code}', '{self.name}', '{self.semester}' '{self.year}')"

class Teacher(db.Model):
    __tablename__ = 'Teacher'
    tid = db.Column(db.Integer, primary_key = True)
    course_id = db.Column(db.Integer, db.ForeignKey('Course.cid') , nullable = False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('User.uid') , nullable = False)
    
    feedback = db.relationship("Feedback", backref = "feedbackTo", lazy = True)
    smile = db.relationship('Smile', backref = 'postedby')

    def __repr__(self):
        return f"Teacher('{self.course_id}', '{self.teacher_id}')"

class Student(db.Model):
    __tablename__ = 'Student'
    sid = db.Column(db.Integer, primary_key = True)
    course_id = db.Column(db.Integer, db.ForeignKey('Course.cid') , nullable = False)
    student_id = db.Column(db.Integer, db.ForeignKey('User.uid') , nullable = False)

    grade = db.relationship("Grade", backref = "gradeFor", lazy = True)
    feedback = db.relationship("Feedback", backref = "feedbackFrom", lazy = True)


    def __repr__(self):
        return f"Student('{self.course_id}', '{self.student_id}')"

class Assignment(db.Model):
    __tablename__ = 'Assignment'
    aid = db.Column(db.Integer, primary_key = True)
    course_id = db.Column(db.Integer, db.ForeignKey('Course.cid') , nullable = False)
    name = db.Column(db.String(20), nullable = False)
    outof = db.Column(db.Integer, nullable = False)
    weight = db.Column(db.Float, nullable = False)
    due = db.Column(db.DateTime)

    grade = db.relationship("Grade", backref = "gradeForAsmt", lazy = True)

    __table_args__ = (
        db.UniqueConstraint('course_id', 'name'),
    )

    def __repr__(self):
        return f"Assignment('{self.name}')"

class Grade(db.Model):
    __tablename__ = 'Grade'
    gid = db.Column(db.Integer, primary_key = True)
    student_id = db.Column(db.Integer, db.ForeignKey('Student.sid') , nullable = False)
    asmt_id = db.Column(db.Integer, db.ForeignKey('Assignment.aid') , nullable = False)
    grade = db.Column(db.Float)


    regrade = db.relationship("Regrade", backref = "regradeFor", lazy = True)

    def __repr__(self):
        return f"Grade('{self.student_id}' '{self.asmt_id}')"

class Regrade(db.Model):
    __tablename__ = 'Regrade'
    rid = db.Column(db.Integer, primary_key = True)
    grade_id = db.Column(db.Integer, db.ForeignKey('Grade.gid') , nullable = False)
    reason = db.Column(db.Text, nullable = False)
    resolved = db.Column(db.Boolean, default = False, nullable = False)

    def __repr__(self):
        return f"Regrade('{self.grade_id}' '{self.resolved}')"

class Feedback(db.Model):
    __tablename__ = 'Feedback'
    fid = db.Column(db.Integer, primary_key = True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('Teacher.tid') , nullable = False)
    student_id = db.Column(db.Integer, db.ForeignKey('Student.sid') , nullable = False)
    category = db.Column(db.String(30), nullable = False, default = "General")
    anonymous = db.Column(db.Boolean, default = True, nullable = False)
    feedback = db.Column(db.Text, nullable = False)

    def __repr__(self):
        return f"Feedback('{self.teacher_id}' '{self.category}')"

class Smile(db.Model):
    __tablename__ = "Smile"
    hid = db.Column(db.Integer, primary_key = True)
    title = db.Column(db.String(20), nullable = False)
    link = db.Column(db.Text)
    type = db.Column(db.String(10))
    desc = db.Column(db.Text)
    date_posted = db.Column(db.DateTime, nullable = False, default = datetime.utcnow)
    posted_by = db.Column(db.Integer, db.ForeignKey('Teacher.tid'), nullable = False)

    def __repr__(self):
        return f"Smile('{self.date_posted}' '{self.title}')"



# ROUTING

    #SIMPLE PAGES
@app.route("/")
@app.route("/home")
def home():
    course = Course.query.get(1) # this is just to show that the website can be modified to show different courses, controlled by admin
    name = ''
    if session.get('username') :
        user = User.query.filter_by(username = session.get('username')).first()
        name = user.firstname
        
        return render_template('index.html', courseCode = course.code, courseName = course.name, courseSession = course.semester + " " + course.year, pagename = 'Home', name = name)
    else:
        return render_template('index.html', courseCode = course.code, courseName = course.name, courseSession = course.semester + " " + course.year, pagename = 'Home', name = name)


@app.route('/logout')
def logout():
    session.pop('username', default = None)
    session.pop('type', default = None)
    flash("You have been logged out", "Notice")
    return redirect(url_for('home'))

@app.route("/syllabus")
def syllabus():
    return render_template("syllabus.html", pagename = 'Syllabus')

@app.route("/courseteam")
def courseteam():
    return render_template("courseteam.html", pagename = 'Course Team')

@app.route("/dailysmile", methods = ["POST", "GET"])
def dailysmile():
    if request.method == "GET":
        smiles = Smile.query.join(Teacher, Teacher.tid == Smile.posted_by).join(User, User.uid == Teacher.teacher_id).add_columns(User.firstname, User.lastname, Smile.title, Smile.link, Smile.type, Smile.desc, Smile.posted_by, Smile.date_posted, Smile.hid).order_by(Smile.date_posted.desc()).all()
        return render_template("dailysmile.html", pagename = '😄 Daily Smile', smiles = smiles)
    else:
        if session.get('type') == "Instructor":
            title = request.form["title"]
            link = request.form['link']
            type = request.form['stype']
            desc = request.form['desc']
            user = Teacher.query.join(User, User.uid == Teacher.teacher_id).filter(User.username == session.get('username')).first()
            smile = Smile(title = title, link = link, type = type, desc = desc, posted_by = user.tid)
            db.session.add(smile)
            db.session.commit()
            flash("New Smile added!", "Notice")
            return redirect(url_for('dailysmile'))

@app.route('/feedback', methods = ['GET', 'POST'])
def feedback():
    if session.get('username'):
        if session.get('type') == "Instructor":
            if request.method == "GET":
                teacher = Teacher.query.join(User, User.uid == Teacher.teacher_id).filter(User.username == session.get('username')).first()
                feedback = Feedback.query.join(Student, Feedback.student_id == Student.sid).join(User, User.uid == Student.student_id).add_columns(Feedback.feedback, Feedback.category,Feedback.anonymous, User.username).filter(Feedback.teacher_id == teacher.tid).order_by(Feedback.fid).all()  
                return render_template("feedback.html", pagename = 'Feedback', feedback = feedback, searchterm = "")
            else:
                search = ""
                if request.form.get('search'):
                    search = request.form.get('search')
                teacher = Teacher.query.join(User, User.uid == Teacher.teacher_id).filter(User.username == session.get('username')).first()

                feedback = Feedback.query.join(Student, Feedback.student_id == Student.sid).join(User, User.uid == Student.student_id).add_columns(Feedback.feedback, Feedback.category,Feedback.anonymous, User.username).filter(Feedback.teacher_id == teacher.tid).filter(or_(Feedback.category.like("%"+search+"%"), Feedback.feedback.like("%"+search+"%"))).order_by(Feedback.fid).all()  
                flash(search, "Results for")
                return render_template("feedback.html", pagename = 'Feedback', feedback = feedback , searchterm = search)

        else:
            if request.method == "GET":
                instructors = Teacher.query.join(User, User.uid == Teacher.teacher_id).add_columns(User.firstname, User.lastname, Teacher.tid).filter(Teacher.course_id == 1).order_by(User.firstname).all()
                return render_template("feedback.html", pagename = 'Feedback', instructors = instructors)
            else:
                instructortid = request.form['instructor']
                category = request.form['category']
                anonymous = 1 if request.form['anonymous'] == "Yes" else 0
                feedback = request.form['feedback']
                student = Student.query.join(User, User.uid == Student.student_id).filter(User.username == session.get('username')).first()
                if instructortid == "all":
                    instructors = Teacher.query.join(User, User.uid == Teacher.teacher_id).add_columns(User.firstname, User.lastname, Teacher.tid).filter(Teacher.course_id == 1).order_by(User.firstname).all()
                    for instructor in instructors:
                        feed = Feedback(teacher_id = instructor.tid, student_id = student.sid, category = category, anonymous = anonymous, feedback = feedback)
                        db.session.add(feed)
                        db.session.commit()
                else:
                    instructor = Teacher.query.get(instructortid)
                    feed = Feedback(teacher_id = instructor.tid, student_id = student.sid, category = category, anonymous = anonymous, feedback = feedback)
                    db.session.add(feed)
                    db.session.commit()
                    flash("Feedback submitted!", "Notice")
                return redirect(url_for('home'))

    else:
        return render_template("feedback.html", pagename = 'Feedback')
        

@app.route("/lectures")
def lectures():
    return render_template("lectures.html", pagename = 'Lectures')

@app.route("/tutorials")
def tutorials():
    return render_template("tutorials.html", pagename = 'Tutorials')

@app.route("/assignments")
def assignments():
    if session.get('username'):
        if session.get('type') == "Instructor" :
            asmts = Assignment.query.filter_by(course_id = 1).all()
        else:
            asmts = Assignment.query.filter_by(course_id = 1).filter(Assignment.name.like("Assignment%")).all()
        return render_template("assignments.html", pagename = 'Assigmnents', asmts = asmts)
    else:
        return render_template("assignments.html", pagename = 'Assigmnents')



    #LESS SIMPLE PAGES
    #USERS
@app.route("/requestregrade", methods = ['GET', 'POST'])
def requestregrade():

    if request.method == "GET":
        grade = Grade.query.filter_by(gid = request.args['gid']).join(Assignment, Assignment.aid == Grade.asmt_id).add_columns(Assignment.name, Assignment.outof, Assignment.weight, Grade.grade, Grade.gid).first()
        return render_template("request_regrade.html", pagename = "Reqeust Regrade", grade = grade)
    else:
        reason = request.form['reason']
        regrade = Regrade(grade_id = request.args['gid'], reason = reason)
        db.session.add(regrade)
        db.session.commit()
        flash("Regrade request submitted.", "Notice")
        return redirect(url_for('grades'))


    #INSTRUCTORS
@app.route("/add_asmt", methods = ["GET", "POST"])
def add_asmt():
    if request.method == "GET":
        return render_template("add_asmt.html", pagename = "New Assignment")
    else:
        name = request.form['name']
        due = datetime.strptime(request.form['due'], '%Y-%m-%dT%H:%M')
        outof = request.form['outof']
        weight = request.form['weight']
        asmt = (
            name, due, outof, weight
        )
        add_asmt_db(asmt)
        flash("Assignment added.", "Notice")

        return redirect(url_for("assignments"))

    #BOTH
@app.route("/regrades", methods = ["GET", "POST"])
def regrades():
    if request.method == "GET":
        t_user = aliased(User)
        s_user = aliased(User)

        regrades = Regrade.query.join(Grade, Grade.gid == Regrade.grade_id).join(Student, Student.sid == Grade.student_id).join(Assignment, Assignment.aid == Grade.asmt_id).join(Course, Student.course_id == Course.cid).join(Teacher, Teacher.course_id == Course.cid).join(t_user, t_user.uid == Teacher.teacher_id).join(s_user, s_user.uid == Student.student_id).add_columns(Regrade.rid, Grade.gid, Regrade.resolved, Student.sid,  s_user.firstname.label("SFirst"), s_user.lastname.label("SLast"), Assignment.name, Assignment.outof, Grade.grade, Assignment.weight, Regrade.reason).filter(t_user.username == session.get('username')).order_by(Regrade.resolved, Assignment.name)

        return render_template("regrades.html", pagename = 'Regrade Requests', regrades = regrades.all())

    else:
        rid = request.form['rid']
        regrade = Regrade.query.get(rid)
        regrade.resolved = 1 if regrade.resolved == 0 else 0
        db.session.commit()
        flash("Regrade request resolved.", "Notice")

        return redirect(url_for('regrades'))


@app.route("/edit_grade", methods = ["GET", "POST"])
def edit_grade():
    if session.get('type') == "Instructor":
        students = Student.query.filter_by(course_id = 1).join(User, User.uid == Student.student_id).add_columns(User.firstname, User.lastname, Student.sid).order_by(User.lastname)
        if request.method == "GET":
            gid = request.args['gid']
            student = Grade.query.join(Student, Student.sid == Grade.student_id).join(User, User.uid == Student.student_id).add_columns(Student.sid, User.firstname, User.lastname).filter(Grade.gid == gid).first()

            grades = Grade.query.join(Assignment, Assignment.aid == Grade.asmt_id).add_columns(Assignment.aid, Assignment.name, Assignment.outof, Assignment.weight, Grade.gid, Grade.grade).join(Student, Student.sid == Grade.student_id).join(User, User.uid == Student.student_id).filter(Student.sid == student.sid).order_by(Assignment.name).all()

            editgrade = Grade.query.join(Assignment, Assignment.aid == Grade.asmt_id).add_columns(Assignment.aid, Assignment.name, Assignment.outof, Assignment.weight, Grade.gid, Grade.grade).join(Student, Student.sid == Grade.student_id).join(User, User.uid == Student.student_id).filter(Student.sid == student.sid).filter(Grade.gid == gid).order_by(Assignment.name).first()

            regrades = db.session.query(Regrade.grade_id, func.count(Regrade.rid).label("count")).join(Grade, Grade.gid == Regrade.grade_id).join(Student, Student.sid == Grade.student_id).where(Student.sid == student.sid).where(Regrade.resolved == 0).group_by(Grade.gid).all()
            average = 0
            num = 0 
            mark = 0
            for grade in grades:   
                if grade.grade != None:
                    average += grade.grade/grade.outof*100
                    num += 1
                    mark += grade.grade/grade.outof*grade.weight
            if num > 0:
                average = average / num
            sum_info = ( round(average, 2), round(mark, 2)) 
            return render_template("grades.html", pagename = 'Grades', students = students, grades = grades, sum_info = sum_info, studentshow = student, state = "edit", edittask = editgrade, regrades = regrades)
        else:
            newgrade = request.form['newgrade']
            gid = request.args['gid']
            grade = Grade.query.get(gid)
            grade.grade = newgrade
            db.session.commit()
            student = Grade.query.join(Student, Student.sid == Grade.student_id).join(User, User.uid == Student.student_id).add_columns(Student.sid, User.firstname, User.lastname).filter(Grade.gid == gid).first()
            flash("Grade changed.", "Notice")
            
            return redirect(url_for('grades', sid = student.sid))

    else:
        return redirect(url_for('grades'))


@app.route("/grades", methods = ['GET', 'POST'])
def grades():
    if session.get('type') == "Instructor":
        students = Student.query.filter_by(course_id = 1).join(User, User.uid == Student.student_id).add_columns(User.firstname, User.lastname, Student.sid).order_by(User.lastname)
        if request.method == "GET":
            sid = students.first().sid
            if request.args.get('sid'):
                sid = request.args["sid"]
             
            student = students.filter(Student.sid == sid).first()                
            grades = Grade.query.join(Assignment, Assignment.aid == Grade.asmt_id).add_columns(Assignment.aid, Assignment.name, Assignment.outof, Assignment.weight,  Grade.gid,Grade.grade).join(Student, Student.sid == Grade.student_id).join(User, User.uid == Student.student_id).filter(Student.sid == student.sid).order_by(Assignment.name).all()

            regrades = db.session.query(Regrade.grade_id, func.count(Regrade.rid).label("count")).join(Grade, Grade.gid == Regrade.grade_id).join(Student, Student.sid == Grade.student_id).where(Student.sid == student.sid).where(Regrade.resolved == 0).group_by(Grade.gid).all()
            average = 0
            num = 0 
            mark = 0
            for grade in grades:   
                if grade.grade != None:
                    average += grade.grade/grade.outof*100
                    num += 1
                    mark += grade.grade/grade.outof*grade.weight
            if num > 0:
                average = average / num
            sum_info = ( round(average, 2), round(mark, 2)) 
            return render_template("grades.html", pagename = 'Grades', students = students, grades = grades, sum_info = sum_info, studentshow = student, state = "view", regrades = regrades)
        else:
            student_id = request.form['student']
            return redirect(url_for('grades', sid = student_id))
            
    else:
        if request.method == "GET":

            grades = Grade.query.join(Assignment, Assignment.aid == Grade.asmt_id).add_columns(Assignment.name, Assignment.outof, Assignment.weight, Assignment.due, Grade.grade).join(Student, Student.sid == Grade.student_id).join(User, User.uid == Student.student_id).filter_by(username = session.get('username')).order_by(Assignment.name).all()
            average = 0
            num = 0 
            mark = 0
            for grade in grades:   
                if grade.grade != None:
                    average += grade.grade/grade.outof*100
                    num += 1
                    mark += grade.grade/grade.outof*grade.weight
            if num > 0:
                average = average / num
            sum_info = ( round(average, 2), round(mark, 2))
            return render_template("grades.html", pagename = "Grades", grades = grades, sum_info = sum_info)

        else:
            gradeID = request.form.get('gradeID')
            grade = Grade.query.filter_by(gid = gradeID).join(Assignment, Assignment.aid == Grade.asmt_id).add_columns(Assignment.name, Assignment.outof, Assignment.weight, Grade.grade).first()
            return redirect(url_for('requestregrade', gid = gradeID))
    

@app.route("/login", methods = ["GET", "POST"])
def login():
    if request.method == "GET":
        if 'username' in session:
            flash("You are already logged in.", "Notice")
            return redirect(url_for("home"))
        else:
            return render_template('login.html', pagename = 'Login')
    else:
        uname = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username = uname).first()
        if not user or not bcrypt.check_password_hash(user.password, password):
            flash("Login failed. Please check your details and try again, or register a new account", 'error')
            return render_template('login.html', pagename = 'Login')
        else:
            student = Student.query.filter_by(student_id = user.uid, course_id = 1).first()
            teacher = Teacher.query.filter_by(teacher_id = user.uid, course_id = 1).first()
            if student:
                session['username'] = user.username
                session['type'] = "Student"
                flash("Logged in as Student.", "Notice")
                return redirect(url_for("home"))
            elif teacher:
                session['username'] = user.username
                session['type'] = "Instructor"
                flash("Logged in as Instructor.", "Notice")
                return redirect(url_for("home"))
            else:
                flash("Login failed. You do not have access to this course", 'error')
                return render_template('login.html', pagename = 'Login')


@app.route("/register", methods = ["GET", "POST"])
def register():
    if session.get('username'):
        flash("You are already registered", "Notice")
        return redirect(url_for('home'))
    else:
        if request.method == "GET":
            return render_template('register.html', pagename = 'Register')
        else:
            hashed_password = bcrypt.generate_password_hash(request.form["password"]).decode("utf-8")
            if bcrypt.check_password_hash(hashed_password, request.form["confirmpassword"]):
                fname = request.form['firstname']
                lname = request.form['lastname']
                uname = request.form['username']
                email = request.form['username']
                type = request.form["account_type"] 
                new_user = (
                    fname, lname, uname, email, type, hashed_password
                )
                try:
                    add_user(new_user)
                    session['username'] = uname
                    session['type'] = type
                    flash("Registered as " + type, "Notice")
                    return redirect(url_for('home'))
                except SQLAlchemyError as e:
                    flash("Account exists already. Log in instead or use a different username/email.", "error")
                    return render_template("register.html", pagename = 'Register')
                
            else:
                flash("Password did not match. Please try again", "error")
                return render_template('register.html', pagename = 'Register')


# HELPER FUNCTIONS
def add_user(new_user):
    user = User(firstname = new_user[0], lastname = new_user[1], username = new_user[2], email = new_user[3], password = new_user[5])
    db.session.add(user)
    db.session.commit()
    if new_user[4] == "Student":
        for user in db.session.query(User).filter(User.username == new_user[2]):
            student = Student(course_id = 1, student_id = user.uid)
            db.session.add(student)
            db.session.commit()

            tasks = Assignment.query.filter_by(course_id = 1).all()
            student_db = Student.query.filter_by(student_id = user.uid).first()
            for task in tasks:
                grade = Grade(student_id = student_db.sid, asmt_id = task.aid)
                db.session.add(grade)
                db.session.commit()
    else:
        for user in db.session.query(User).filter(User.username == new_user[2]):
            instructor = Teacher(course_id = 1, teacher_id = user.uid)
            db.session.add(instructor)
            db.session.commit()


def add_asmt_db(new_asmt):
    asmt = Assignment(name = new_asmt[0], due = new_asmt[1], outof = new_asmt[2], weight = new_asmt[3], course_id = 1)
    db.session.add(asmt)
    db.session.commit()

    students = Student.query.filter_by(course_id = 1).all()
    asmt_db = Assignment.query.filter_by(name = new_asmt[0]).first()
    for student in students:
        grade = Grade(student_id = student.sid, asmt_id = asmt_db.aid)
        db.session.add(grade)
        db.session.commit()


if __name__ == '__main__':
    app.run(debug = True)
