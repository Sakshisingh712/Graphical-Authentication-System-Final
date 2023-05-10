from flask import Blueprint, render_template, redirect, url_for, request, flash,session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required
from .models import User
from . import db
import string
import speech_recognition as sr
from PIL import Image, ImageDraw, ImageFont
import random
import smtplib
from email.mime.text import MIMEText
import io
import string
from PIL import Image, ImageDraw, ImageFont
import random
from flask import Flask, request, jsonify
import base64
import datetime

reset_tokens = {}
users = {}
spoken_text=''
global original_text
original_text = ''
auth = Blueprint('auth', __name__)
def generate_password():
    chars = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(chars) for _ in range(10))

@auth.route('/signup')
def signup():
    #Grahical---Password---Logic to confuse hacker
    N = 6
    images_ = random.sample(range(10, 46), N * N)
    images = []
    for i in range(0, N * N, N):
        images.append(images_[i:i + N])
    return render_template('signup.html',images=images)

@auth.route('/login')
def login():
    #Grahical---Password---Logic to confuse hacker
    N = 6
    images_ = random.sample(range(10, 46), N * N)
    images = []
    for i in range(0, N * N, N):
        images.append(images_[i:i + N])
    return render_template('login.html',images=images)

@auth.route('/signup', methods=['POST'])
def signup_post():
    email = request.form.get('email')
    name = request.form.get('name')
    if(request.form.get('row') and request.form.get('column')):
        row = request.form.get('row')
        col = request.form.get('column')
        password = row+col
        print(password, ".....")
    else:
        password_1 = sorted(request.form.getlist('password'))
        password_1 = ''.join(map(str, password_1))
        if len(password_1) < 8:
            flash("password must be minimum 4 selections")
            return redirect(url_for('auth.signup'))
        else:
            password = password_1

   # if this returns a user, then the email already exists in database
    user = User.query.filter_by(email=email).first()

    if user: # if a user is found, we want to redirect back to signup page so user can try again
        flash('Email address already exists')
        return redirect(url_for('auth.signup'))

    # create a new user with the form data. Hash the password so the plaintext version isn't saved.
    new_user = User(email=email, name=name, password=generate_password_hash(password, method='sha256'))
    # add the new user to the database
    db.session.add(new_user)
    db.session.commit()
    return redirect(url_for('auth.login'))

@auth.route('/login', methods=['POST'])
def login_post():
    email = request.form.get('email')
    if(request.form.get('row-column')):
        password = request.form.get('row-column')
        print("****"+password+"*******",".....")

    else:
        password_1= sorted(request.form.getlist('password'))
        password_1 =''.join(map(str, password_1))
        if len(password_1) < 8:
            flash("password must be minimum 4 selections")
            return redirect(url_for('auth.signup'))
        else:
            password = password_1
    remember = True if request.form.get('remember') else False
    user = User.query.filter_by(email=email).first()
    # check if the user actually exists
    # take the user-supplied password, hash it, and compare it to the hashed password in the database
    if not user or not check_password_hash(user.password, password):
        flash('Please check your login details and try again.')
        return redirect(url_for('auth.login'))  # if the user doesn't exist or password is wrong, reload the page
    # if the above check passes, then we know the user has the right credentials
    login_user(user, remember=remember)
    return redirect(url_for('auth.obscured_image'))

@auth.route('/obscured_image')
def obscured_image():
    # your code to generate and display the obscured image
       # Set up image size and background color
    img_width = 450
    img_height = 200
   
    background_color = (random.randint(200, 255), random.randint(200, 255), random.randint(200, 255))
    # Create a new image with the given size and background color
    img = Image.new('RGB', (img_width, img_height), background_color)
    # Get a drawing context for the image
    draw = ImageDraw.Draw(img)
    # Set up the font and text for the image
    font_size = 48
    font_color = (0, 0, 0)
    font = ImageFont.truetype("arial.ttf", font_size)
    # Example usage
    global original_text
    original_text = "Testing is going on"
    # original_text=''.join(random.choice(string.ascii_letter) for _ in range(10))
    # Get the size of the text and calculate its position in the center of the image
    text_width, text_height = draw.textsize(original_text, font)
    text_x = (img_width - text_width) // 2
    text_y = (img_height - text_height) // 2
    # Draw the text on the image
    draw.text((text_x, text_y),original_text, font=font, fill=font_color)
    # Add a watermark to the text
    watermark_text = "This is sample text"
    watermark_font_size = 42
    watermark_font_color = (128,128,128)
    watermark_font = ImageFont.truetype("arial.ttf", watermark_font_size)
    watermark_width, watermark_height = draw.textsize(watermark_text, watermark_font)
    watermark_x = ((text_x + text_width)/15)
    watermark_y = ((text_y + text_height) - watermark_height)
    draw.text((watermark_x, watermark_y), watermark_text, font=watermark_font, fill=watermark_font_color, rotate =45)
    img.save("project\static\Obscured_image.png")
    # Display the image
    #img.show()
    original_text=original_text.lower().replace(' ', '-')
    return render_template('obscured_image.html')

@auth.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        user = User.query.filter_by(email=email).first()
        if user:
            
            # Generate a new random temporary password for the user
            temp_password = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(12))
            # Hash the temporary password using SHA256
            hashed_temp_password = generate_password_hash(temp_password)
            user.password = hashed_temp_password
            db.session.commit()
            # Generate a new random password reset token for the user
            token = ''.join(random.choice('0123456789abcdef') for _ in range(32))
            import datetime
            reset_tokens[token] = {'email': email, 'timestamp': datetime.datetime.now() + datetime.timedelta(minutes=10)}

            # Send a password reset link to the user via email
            msg = MIMEText(f'Click the following link to reset your password: {url_for("auth.reset_password", token=token, _external=True)}')
            msg['Subject'] = 'Password Reset Request'
            msg['From'] = 'noreply@example.com'
            msg['To'] = email
            with smtplib.SMTP('smtp.gmail.com', port=587) as smtp:
                smtp.starttls()
                smtp.login('roshanladdha2424@gmail.com', 'azrqyuqqhtgvgskz')
                smtp.send_message(msg)
            flash('A password reset link has been sent to your email')
        else:
            flash('Email address not found')
    return render_template('forgot_password.html')

@auth.route('/reset_password')
def reset_password():
    #Grahical---Password---Logic to confuse hacker
    N = 6
    images_ = random.sample(range(10, 46), N * N)
    images = []
    for i in range(0, N * N, N):
        images.append(images_[i:i + N])
    return render_template('reset_password.html',images=images)

@auth.route('/reset_password', methods=['POST'])
def reset_password_post():
    email = request.form.get('email')
    # name = request.form.get('name')
    temporary_password=request.form.get('temporary_password')
    if(request.form.get('row') and request.form.get('column')):
        row = request.form.get('row')
        col = request.form.get('column')
        password = row+col
        print(password, ".....")
    else:
        password_1 = sorted(request.form.getlist('password'))
        password_1 = ''.join(map(str, password_1))
        if len(password_1) < 8:
            flash("password must be minimum 4 selections")
            return redirect(url_for('auth.reset_password'))
        else:
            password = password_1

   # if this returns a user, then the email already exists in database
    user = User.query.filter_by(email=email).first()  

    # # add the new password to the database
    user.password = generate_password_hash(password)
    # db.session.add(user)
    db.session.commit()
    return redirect(url_for('auth.login'))

@auth.route('/verify', methods=['POST'])
def verify():
    global original_text
    input_text = request.form['text'].lower().replace(' ', '-')
    print(original_text)
    print(input_text)
    if input_text == original_text:
        print(input_text)
        session['is_authenticated'] = True
        return 'authenticated'
    else:
        return 'authentication-failed'

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))

