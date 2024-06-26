""" Flask app """
from flask import Flask, render_template, request, session, redirect, url_for
from api.db import db # Import Database setup
from api.models import ma
from api.models import User
from api.blueprint import app_views
import os
from api.models import Pet
import requests
from flask_cors import CORS  # Import the CORS module
from flask_bcrypt import Bcrypt  # Import bcrypt for pswd hashing
from flask import jsonify
from api.users import get_user_pets


def create_app():

    app = Flask(__name__)
    app.secret_key = 'PetPhysique' # for session management

    pet_bmi_ranges = {
        "Abyssinian": (14.34, 17.67),
        "Africanis": (72.12, 78.45),
        "American Shorthair": (15.35, 17.67),
        "Bengal": (100, 112),
        "Birman": (80, 100),
        "British Shorthair": (33.33, 37),
        "Basenji": (62.33, 64.9),
        "Beagle": (65.44, 82.64),
        "Boerboel": (191.14, 216.84),
        "Boxer": (74.34, 79.67),
        "Bulldog": (156, 187),
        "Bull Terrier": (60, 75),
        "Chihuahua": (17.5, 23),
        "Cocker Spaniel": (39, 48),
        "Dachshund": (175 , 295.86),
        "Doberman": (75, 90),
        "German Shepherd": (75, 90),
        "Golden Retriever": (91, 97),
        "Labrador Retriever": (82, 90),
        "Maine Coon": (20, 25),
        "Manx": (20, 25),
        "Ocicat": (14, 18),
        "Poodle": (35, 50),
        "Pug": (18, 22),
        "Rottweiler": (75, 90),
        "Russian Blue": (18, 25),
        "Siberian Husky": (35, 50),
        "Somali": (8, 12),
        "Sphynx": (96, 126)
        
        # Add more pet types and their healthy BMI ranges here
    }


    """Database configuration"""
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'data.sqlite')

    """Sqlalchemy track modification"""
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    """Initialize db"""
    db.init_app(app)
    """Initialize marshmallow"""
    ma.init_app(app)
    """Register blueprint"""
    app.register_blueprint(app_views)
    """implement cors to all origin"""
    cors = CORS(app, resources={r"/api/*": {"origins": "*"}})
    """nitialize bcrypt"""
    bcrypt = Bcrypt(app)


    """landing page"""
    @app.route('/')
    def landing_page():
        return render_template("landing_page.html")
    """home page"""
    @app.route('/home')
    def home():
        return render_template("home.html")

    """sign in"""
    @app.route('/login', methods=["POST", "GET"])
    def login():
        if request.method == 'POST':
            # get user data from login form
            email = request.form.get('email')
            password = request.form.get('password')

            # Check if email/email and password are provided
            if not email or not password:
                return render_template("login.html", error='Missing username/email or password')

            # Query the database for the user
            user = User.query.filter((User.password == password) | (User.email == email)).first()

            # Check if user exists and password is correct
            if user and bcrypt.check_password_hash(user.password, password):
                # Store user's information in session
                session['user_id'] = user.id
                session['username'] = user.username  # Store username in session
                session['email'] = user.email
                # Redirect to dashboard or profile page
                return redirect(url_for('dashboard'))
            else:
                return render_template('login.html', error='Invalid username/email or password')

        # If method is GET, render the login form
        return render_template('login.html')




    """sign up"""
    @app.route('/sign-up', methods=["POST", "GET"])
    def signin():
        if request.method == "POST":
            # Get data from request
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')

            # if username/email already exists render login page
            if User.query.filter_by(username=username).first() or User.query.filter_by(email=email).first():
                return render_template('login.html', error='User already exists. Please log in.')

            # If not, reate a new user
            new_user = User(username=username, email=email, password=bcrypt.generate_password_hash(password).decode('utf-8'))
            db.session.add(new_user)
            db.session.commit()

            # Store user's ID in session
            session['user_id'] = new_user.id

            # Redirect to dashboard (We have to change this to profile page)
            return redirect(url_for('/home'))

        else:
            return render_template("signup.html")
        
    """sign out"""
    @app.route('/logout')
    def logout():
        # clear user session
        session.clear()
        return redirect(url_for('home'))

    """dashboard"""
    @app.route('/dashboard')
    def dashboard():
        user_id = session.get('user_id')  # Get the user_id from the session
        username = session.get('username')
        email = session.get('email')
        # Assuming you have user_pets defined somewhere
        user_pets = ...

        # Pass user_id to the template
        return render_template("dashboard.html", user_id=user_id, username=username, email=email, user_pets=user_pets)


    """About us page"""
    @app.route('/about-us')
    def about_us():
        return render_template('about_us.html')




    """show user"""
    @app.route('/user-info')
    def show_user():
        return render_template('show_user.html')

    @app.route('/my-pets')
    def show_pets():
        user_id = session.get('user_id')
        if user_id is None:
            return redirect(url_for('login'))
        url = url_for('app_views.get_user_pets', user_id=user_id, _external=True)
        response = requests.get(url)
        if response.status_code == 200:
            user_pets = response.json()
            for pet in user_pets:
                bmi = pet['weight'] / (pet['height'] ** 2)
                healthy_bmi_range = pet_bmi_ranges.get(pet['type'])
                if healthy_bmi_range:
                    min_bmi, max_bmi = healthy_bmi_range
                    if min_bmi <= bmi <= max_bmi:
                        pet['health_status'] = 'healthy'
                    elif bmi < min_bmi:
                        pet['health_status'] = 'underweight'
                    else:
                        pet['health_status'] = 'overweight'
                    # Calculate health percentage
                    if pet['health_status'] == 'healthy':
                        pet['health_percentage'] = 100
                    elif pet['health_status'] == 'underweight':
                        pet['health_percentage'] = 50
                    else:
                        pet['health_percentage'] = 25
        else:
            return render_template('error.html', error='Failed to fetch user pets')
        return render_template('show_pets.html', user_pets=user_pets)


    """update pet"""
    @app.route('/update-pet/<int:pet_id>', methods=['GET', 'POST'])
    def update_pet(pet_id):
        if request.method == 'GET':
            # Retrieve the pet from the database based on the provided pet_id
            pet = Pet.query.get(pet_id)
            if pet is None:
                # If the pet with the given ID doesn't exist, return a 404 error
                return render_template('error.html', error='Pet not found'), 404

            # Render the update_pet.html template and pass the pet_id as a context variable
            return render_template('update_pet.html', pet_id=pet_id)
        elif request.method == 'POST':
            # Handle the form submission to update the pet's information
            weight = request.form.get('weight')
            height = request.form.get('height')
            
            # Update the pet's weight and height in the database
            pet = Pet.query.get(pet_id)
            if pet:
                pet.weight = weight
                pet.height = height
                db.session.commit()
                return redirect(url_for('show_pets'))
            else:
                return render_template('error.html', error='Pet not found'), 404

    """delete pet"""
    @app.route('/delete-pet/<int:pet_id>', methods=['POST'])
    def delete_pet(pet_id):
        if request.form.get('_method') == 'DELETE':
            # Handle the deletion logic here
            pet = Pet.query.get(pet_id)
            if pet:
                db.session.delete(pet)
                db.session.commit()
                return redirect(url_for('show_pets'))
            else:
                return render_template('error.html', error='Pet not found'), 404
        else:
            return "Method not allowed", 405


    """create pet"""
    @app.route('/create-pet', methods=['GET'])
    def create_pet_form():
        return render_template('create_pet.html')

    """infomation"""
    @app.route('/info')
    def info():
        return render_template('info.html')

    """q&a"""
    @app.route('/questions')
    def questions():
        return render_template('questions.html')

    @app.errorhandler(404)
    def page_not_found(error):
        return render_template('404.html'), 404
    
    return app
app = create_app()

# Run the Flask app
if __name__ == '__main__':
    # Importing db here ensures it's imported within the application context.
    from app import db
    # Create the database tables based on the defined models
    with app.app_context():
        db.create_all()
    app.run(debug=True)
