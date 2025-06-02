from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
import csv
import pandas as pd
import matplotlib.pyplot as plt  
import base64
from io import BytesIO
import seaborn as sns


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
db = SQLAlchemy(app)


def generate_figure():
    df = pd.read_csv('adicciones.csv')
    return df


class Persona(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    age = db.Column(db.Integer)
    gender = db.Column(db.String(20))
    smokes_per_day = db.Column(db.Integer)
    drinks_per_week = db.Column(db.Integer)
    age_started_smoking = db.Column(db.Integer)
    age_started_drinking = db.Column(db.Integer)
    attempts_to_quit_smoking = db.Column(db.Integer)
    attempts_to_quit_drinking = db.Column(db.Integer)
    has_health_issues = db.Column(db.Boolean)
    mental_health_status = db.Column(db.String(50))
    bmi = db.Column(db.Float)
    social_support = db.Column(db.String(50))
    therapy_history = db.Column(db.String(50))


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
            )
            db.session.add(persona)
        db.session.commit()
        return redirect('/')
    return f"Error al cargar archivo: {str(e)}", 500


@app.route('/graficos')
def graficos():
    personas = Persona.query.all()

    plt.figure(figsize=(12, 5))

    cigarrillos = [p.smokes_per_day for p in personas]
    plt.subplot(1,2,1)
    plt.hist(cigarrillos, bins=10, color='grey', edgecolor='black')
    plt.title('Cigarrillos diario')
    plt.xlabel('Cigarrillos')
    plt.ylabel('Frecuencia')
    

    tragos = [p.drinks_per_week for p in personas]
    plt.subplot(1,2,2)
    plt.hist(tragos, bins=10, color='blue', edgecolor='black')
    plt.title('Consumo de alcohol semanalmente')
    plt.xlabel('Consumo')
    plt.ylabel('Frecuencia')


    img = BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode()
    plt.close()

    return render_template('graficos.html', plot_url=plot_url)




@app.route('/consumos')
def consumo_vs_salud():
    personas = Persona.query.filter(Persona.smokes_per_day, Persona.bmi, Persona.gender.in_(["Male", "Female"])).all()
    dia_fumar = [persona.smokes_per_day for persona in personas]
    imc = [persona.bmi for persona in personas]


    plt.figure(figsize=(12, 5))
    sns.regplot(x = dia_fumar, y=imc, color='salmon', scatter_kws={'alpha':0.4}, line_kws={'color': 'black'})
    plt.title('Cigarrillos vs BMI') #es una relacion de cuanto fuma una persona en base al bmi
    plt.xlabel('Cigarrillos por día')
    plt.ylabel('Índice de Masa Corporal')

        
    img = BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode('utf-8')
    plt.close()
    
    return render_template('fumadores.html', plot_url=plot_url)


@app.route('/max_min')
def analisis_max_min():
    personas = Persona.query.all()
    edades_fumar = [p.age_started_smoking for p in personas ]
        
    plt.figure(figsize=(12, 5))
        
    edad_max_fumar = max(edades_fumar)
    edad_min_fumar = min(edades_fumar)
    edad_prom_fumar = sum(edades_fumar) / len(edades_fumar)
            
    categorias = ['Máxima edad', 'Mínima edad', 'Edad promedio']
    valores = [edad_max_fumar, edad_min_fumar, edad_prom_fumar]
    colores = ['lightcoral', 'lightgreen', 'lightblue']

    bars = plt.bar(categorias, valores, color=colores)
    
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height,
            f'{int(height)} años',
                ha='center', va='bottom')



    plt.title('Edad de Inicio en el Consumo de Tabaco')
    plt.ylabel('Edad (años)')
    plt.grid(True, axis='y', linestyle='--', alpha=0.7)
        

    img = BytesIO()
    plt.savefig(img, format='png', bbox_inches='tight')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode('utf-8')
    plt.close()

    return render_template('maxymin.html', plot_url=plot_url)


if __name__ == "__main__":
    app.run(debug=True)
