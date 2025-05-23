from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
import io
import matplotlib.pyplot as plt
import base64
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
    smokes_per_day = db.Column(db.Integer)
    drinks_per_week = db.Column(db.Integer)
    age_started_smoking = db.Column(db.Integer)
    age_started_drinking = db.Column(db.Integer)
    attempts_to_quit_smoking = db.Column(db.Integer)
    attempts_to_quit_drinking = db.Column(db.Integer)
    has_health_issues = db.Column(db.Boolean)
    mental_health_status = db.Column(db.String(50))
    therapy_history = db.Column(db.String(50))


with app.app_context():
    db.create_all()



@app.route('/')
def index():
    personas = Persona.query.all()
    return render_template('index.html', personas=personas)



@app.route('/cargar', methods=['POST'])
def cargar_csv():
    if 'file' not in request.files:
        return "No se envió archivo", 400

    file = request.files['file']
    if file.filename == '':
        return "Nombre de archivo vacío", 400

    try:
        if file.filename.endswith('.csv'):
            df = pd.read_csv(file)
        elif file.filename.endswith('.xlsx'):
            df = pd.read_excel(file)
        else:
            return "Formato no soportado. Solo .csv o .xlsx", 400

        for _, row in df.iterrows():
            persona = Persona(
                id=int(row['id']),
                name=row['name'],
                age=int(row['age']),
                gender=row['gender'],
                country=row['country'],
                smokes_per_day=int(row['smokes_per_day']),
                drinks_per_week=int(row['drinks_per_week']),
                age_started_smoking=int(row['age_started_smoking']),
                age_started_drinking=int(row['age_started_drinking']),
                attempts_to_quit_smoking=int(row['attempts_to_quit_smoking']),
                attempts_to_quit_drinking=int(row['attempts_to_quit_drinking']),
                has_health_issues=bool(row['has_health_issues']),
                mental_health_status=row['mental_health_status'],
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
