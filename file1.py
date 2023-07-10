from flask import Flask, render_template, request, session, redirect   # render_template is used to link html and similar pages to python code
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
import math
from flask_mail import Mail

local_server = True
with open('config.json','r') as c:
    params = json.load(c)["params"]

db = SQLAlchemy()
app = Flask(__name__)
app.secret_key = 'super_secret'
# configure the SQLite database, relative to the app instance folder
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT='465',
    MAIL_USE_SSL=True,
    MAIL_USERNAME=params['gmail_user'],
    MAIL_PASSWORD=params['gmail_password']
)
mail = Mail(app)

if local_server:
    app.config["SQLALCHEMY_DATABASE_URI"] = params['local_uri']
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = params['prod_uri']
db.init_app(app)


class Contact(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    phone_num = db.Column(db.String(14), nullable=False)
    msg = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=True)
    email = db.Column(db.String(120), nullable=False)


class Posts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    slug = db.Column(db.String(21), nullable=False)
    content = db.Column(db.String(120), nullable=False)
    tagline = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=True)
    img_file = db.Column(db.String(12), nullable=True)
    git_link = db.Column(db.String(200), nullable=True)


@app.route('/')
def home():
    posts = Posts.query.filter_by().all()
    last = math.ceil(len(posts) / int(params['no_of_posts']))
    page = request.args.get('page')
    if not str(page).isnumeric():
        page = 1

    page = int(page)
    posts = posts[(page - 1) * int(params['no_of_posts']): (page - 1) * int(params['no_of_posts']) + int(
        params['no_of_posts'])]

    if page == 1:
        prev = "#"
        nex = '/?page=' + str(page + 1)

    elif page == last:
        nex = "#"
        prev = '/?page=' + str(page - 1)
    else:
        prev = '/?page=' + str(page - 1)
        nex = '/?page=' + str(page + 1)

    return render_template('index.html', params=params, posts=posts, prev=prev, nex=nex)  # this how you link html page to python


@app.route('/about')
def about():
    return render_template('about.html', params=params)  # the name in orange color is taken in the html file about. and the
                                          # this name can be edited like we can chage it to name1, name_a etc.


@app.route('/post/<string:post_slug>', methods=['GET'])
def post_route(post_slug):
    post = Posts.query.filter_by(slug=post_slug).first()

    return render_template('post.html', params=params, post=post)


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        # add entry to the db
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        msg = request.form.get('message')

        entry = Contact(name=name, email=email, date=datetime.now(), phone_num=phone, msg=msg)
        db.session.add(entry)
        db.session.commit()
        mail.send_message('New Message from Blog '+name,
                          sender=email,
                          recipients=[params['gmail_user']],
                          body=msg+"\n"+phone
                          )

    return render_template('contact.html', params=params)


@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user' in session and session['user'] == params['admin_user']:
        posts = Posts.query.all()
        return render_template('dashboard.html', params=params, posts=posts)

    if request.method == 'POST':
        # redirect ot admin panel
        username = request.form.get('uname')
        password = request.form.get('pass')
        if username == params['admin_user'] and password == params['admin_password']:
            # set the session variable
            session['user'] = username
            posts = Posts.query.all()
            return render_template('dashboard.html', params=params, posts=posts)
    else:
        return render_template('login.html', params=params)


@app.route('/edit/<string:sno>', methods=['GET','POST'])
def edit(sno):
    if 'user' in session and session['user'] == params['admin_user']:
        if request.method == 'POST':
            box_title = request.form.get('title')
            tagline = request.form.get('tagline')
            slug = request.form.get('slug')
            content = request.form.get('content')
            img_file = request.form.get('img_file')
            git_link = request.form.get('git_link')
            date = datetime.now()

            if sno == '0':
                post = Posts(title=box_title, tagline=tagline, slug=slug, content=content, img_file=img_file,
                             git_link=git_link, date=date)
                db.session.add(post)
                db.session.commit()
            else:
                post = Posts.query.filter_by(sno=sno).first()
                post.title = box_title
                post.tagline = tagline
                post.slug = slug
                post.content = content
                post.img_file = img_file
                post.git_link = git_link
                post.date = date
                db.session.commit()
                return redirect('/edit/'+sno)

        post = Posts.query.filter_by(sno=sno).first()
        return render_template('edit.html', params=params, post=post, sno=sno)


@app.route("/logout")
def logout():
    session.pop("user")
    return redirect('/dashboard')


@app.route("/delete/<string:sno>", methods=['GET','POST'])
def delete(sno):
    if 'user' in session and session['user'] == params['admin_user']:
        post = Posts.query.filter_by(sno=sno).first()
        db.session.delete(post)
        db.session.commit()
    return redirect("/dashboard")


app.run(debug=False, host='0.0.0.0')
