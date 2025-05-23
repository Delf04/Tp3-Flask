from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
import csv
from datetime import datetime
import os
import pandas as pd




app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
db = SQLAlchemy(app)


os.makedirs('static/plots', exist_ok=True)


def generate_figure():
    # Read the CSV file
    df = pd.read_csv('adicciones.csv')
    return df


class Persona(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    age = db.Column(db.Integer)
    gender = db.Column(db.String(20))
    country = db.Column(db.String(100))
    city = db.Column(db.String(100))
    education_level = db.Column(db.String(50))
    employment_status = db.Column(db.String(50))
    annual_income_usd = db.Column(db.Float)
    marital_status = db.Column(db.String(50))
    children_count = db.Column(db.Integer)
    smokes_per_day = db.Column(db.Integer)
    drinks_per_week = db.Column(db.Integer)
    age_started_smoking = db.Column(db.Integer)
    age_started_drinking = db.Column(db.Integer)
    attempts_to_quit_smoking = db.Column(db.Integer)
    attempts_to_quit_drinking = db.Column(db.Integer)
    has_health_issues = db.Column(db.Boolean)
    mental_health_status = db.Column(db.String(50))
    exercise_frequency = db.Column(db.String(50))
    diet_quality = db.Column(db.String(50))
    sleep_hours = db.Column(db.Float)
    bmi = db.Column(db.Float)
    social_support = db.Column(db.String(50))
    therapy_history = db.Column(db.String(50))


with app.app_context():
    db.create_all()
    print("¡Base de datos y tablas creadas correctamente!")



@app.route('/')
def index():
    personas = Persona.query.all()
    return render_template('index.html', personas=personas)



@app.route('/cargar', methods=['POST'])
def cargar_csv():
    file = request.files['file']
    if file and file.filename.endswith('.csv'):
        stream = file.stream.read().decode('utf-8').splitlines()
        reader = csv.DictReader(stream)
        for row in reader:
            persona = Persona(
                id=int(row['id']),
                name=row['name'],
                age=int(row['age']),
                gender=row['gender'],
                country=row['country'],
                city=row['city'],
                education_level=row['education_level'],
                employment_status=row['employment_status'],
                annual_income_usd=float(row['annual_income_usd']),
                marital_status=row['marital_status'],
                children_count=int(row['children_count']),
                smokes_per_day=int(row['smokes_per_day']),
                drinks_per_week=int(row['drinks_per_week']),
                age_started_smoking=int(row['age_started_smoking']),
                age_started_drinking=int(row['age_started_drinking']),
                attempts_to_quit_smoking=int(row['attempts_to_quit_smoking']),
                attempts_to_quit_drinking=int(row['attempts_to_quit_drinking']),
                has_health_issues=row['has_health_issues'].strip().lower() == 'true',
                mental_health_status=row['mental_health_status'],
                exercise_frequency=row['exercise_frequency'],
                diet_quality=row['diet_quality'],
                sleep_hours=float(row['sleep_hours']),
                bmi=float(row['bmi']),
                social_support=row['social_support'],
                therapy_history=row['therapy_history']
            )
            db.session.add(persona)
        db.session.commit()
        return redirect('/')
    except Exception as e:
        return f"Error al cargar archivo: {str(e)}", 500


@app.route('/graficos')
def graficos():
    personas = Persona.query.all()
    edades = [p.age for p in personas]
    cigarrillos = [p.smokes_per_day for p in personas]
    tragos = [p.drinks_per_week for p in personas]

    plt.figure(figsize=(10, 5))
    plt.hist(cigarrillos, bins=10, color='orange', edgecolor='black')
    plt.title('Cigarrillos por Día')
    plt.xlabel('Cigarrillos')
    plt.ylabel('Frecuencia')
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    cig_img = base64.b64encode(img.getvalue()).decode()

    plt.figure(figsize=(10, 5))
    plt.hist(tragos, bins=10, color='blue', edgecolor='black')
    plt.title('Tragos por Semana')
    plt.xlabel('Tragos')
    plt.ylabel('Frecuencia')
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    alcohol_img = base64.b64encode(img.getvalue()).decode()

    return render_template('graficos.html', cig_img=cig_img, alcohol_img=alcohol_img)



if __name__ == "__main__":
    app.run(debug=True)
