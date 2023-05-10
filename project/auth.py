from flask import Blueprint, render_template, redirect, url_for, request, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required
from .models import User
from . import db
#from flask_mail import Mail, Message
import string
import speech_recognition as sr
from PIL import Image, ImageDraw, ImageFont
import random
import io
import string
# set up the microphone
# r = sr.Recognizer()
# mic = sr.Microphone()
from PIL import Image, ImageDraw, ImageFont
import random
from flask import Flask, request, jsonify
import base64
# import spacy
# nlp = spacy.load("en_core_web_sm")




spoken_text=''
original_text=''
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
@login_required
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
    text = "Testing is going on!"
    # Get the size of the text and calculate its position in the center of the image
    text_width, text_height = draw.textsize(text, font)
    text_x = (img_width - text_width) // 2
    text_y = (img_height - text_height) // 2

    # Draw the text on the image
    draw.text((text_x, text_y), text, font=font, fill=font_color)

    # Add a watermark to the text
    watermark_text = "This is sample text."
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
    original_text=text

    return render_template('obscured_image.html')

@auth.route("/compare-audio", methods=["POST"])
def compare_audio():
    # Get the base64-encoded audio file from the request body
    request_data = request.get_json()
    audio_data = base64.b64decode(request_data["audio"])
    
    # Use the SpeechRecognition library to transcribe the audio file into text
    recognizer = sr.Recognizer()
    with io.BytesIO(audio_data) as source:
        audio_data = source.read()
        audio = recognizer.record(source)
        transcribed_text = recognizer.recognize_google(audio)

    # Define the reference text for comparison
    #reference_text = original_text
    transcribed_doc = nlp(transcribed_text)
    reference_doc = nlp(reference_text)
    
    # Check if the transcribed text matches the reference text
    if transcribed_text == reference_text:
        result = {"success": True}
    else:
        result = {"success": False}

    # Return the result as a JSON response
    return jsonify(result)


    # Return the similarity score to the frontend
    
@auth.route('/authentication', methods=['POST'])
@login_required
def authentication():
    # your code to recognize the text from the obscured image and compare with the original text
    if spoken_text  == original_text:
        return redirect(url_for('main.profile'))
    else:
        flash('Sorry, you did not correctly read the text from the image.')
        return redirect(url_for('auth.obscured_image'), flash_duration=5) 


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))

