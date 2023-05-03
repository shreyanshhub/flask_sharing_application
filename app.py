from flask import Flask,session,redirect,url_for,request,render_template,flash,send_file
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail,Message
from io import BytesIO

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///share.sqlite3"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = "share"

db = SQLAlchemy(app)

mail = Mail(app)

app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'paramguy18@gmail.com'
app.config['MAIL_PASSWORD'] = 'htcxdfkpgcczrsla'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

mail = Mail(app)

class User(db.Model):

    id = db.Column("id",db.Integer,primary_key=True)
    username = db.Column("username",db.String(100))
    password = db.Column("password",db.String(100))
    files = db.relationship("File",backref="user")

class File(db.Model):

    id = db.Column("id",db.Integer,primary_key=True)
    file_id = db.Column("file_id",db.String(100),db.ForeignKey("user.username"))
    filename = db.Column("filename",db.String(1000))
    file = db.Column("files",db.LargeBinary)


@app.route("/",methods=["GET","POST"])
def home():
    return render_template("index.html")

@app.route("/register",methods=["GET","POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(username=username).first()

        if user:

            flash("Username already exists")
            return render_template("register.html")

        else:

            user = User(username=username,password=password)

            db.session.add(user)
            db.session.commit()
            flash("User registered successfully")

            return redirect(url_for("login"))

    else:

        return render_template("register.html")

@app.route("/login",methods=["GET","POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(username=username,password=password).first()

        if user:

            session["username"] = username
            flash("User logged in successfully")
            return redirect(url_for("dashboard"))

        else:

            flash("Incorrect username or password")
            return render_template("login.html")

    else:

        if "username" in session:
            flash("User already logged in")
            return redirect(url_for("dashboard"))

        return render_template("login.html")

@app.route("/logout",methods=["GET","POST"])
def logout():

    if "username" in session:

        session.pop("username",None)
        flash("User logged out successfully")
        return redirect(url_for("login"))

    else:

        return redirect(url_for("login"))

@app.route("/dashboard",methods=["GET","POST"])
def dashboard():

    user = User.query.filter_by(username=session["username"]).first()

    if request.method == "POST":

        file1 = request.files["file"]
        filename = request.form["filename"]

        file = File(file=file1.read(),filename=filename,user=user)

        db.session.add(file)
        db.session.commit()

        return redirect(url_for("share",file_id=file.id))

    return render_template("dashboard.html",user=user)

@app.route("/share/<file_id>",methods=["GET","POST"])
def share(file_id):

    file = File.query.filter_by(id=file_id).first()

    if request.method == "POST":

        email = request.form["email"]

        msg = Message(
                'Hello',
                sender ='paramguy18@gmail.com',
                recipients = [str(email)]
               )
        msg.body = "Hi friend, your friend " + str(session["username"]) +" has sent you a file to download " + " Go to this link to download it " + request.host_url + url_for("download",file_id=file_id)
        mail.send(msg)

    return render_template("share_download.html",file_id=file_id)

@app.route("/download/<file_id>")
def download(file_id):

    file = File.query.filter_by(id=file_id).first()
    return send_file(BytesIO(file.file),attachment_filename=file.filename,as_attachment=True)

@app.route("/delete/<user_id>/<file_id>",methods=["GET","POST"])
def delete(user_id,file_id):

    if request.method == "POST":
        user = User.query.filter_by(id=user_id).first()
        file = File.query.filter_by(id=file_id,user=user).first()

        db.session.delete(file)
        db.session.commit()

        return redirect(url_for("dashboard"))

    return render_template("delete.html")

if __name__ == "__main__":

    with app.app_context():
        db.create_all()
        app.run(debug=True)
