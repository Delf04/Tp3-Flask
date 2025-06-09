from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
import matplotlib.pyplot as plt
import base64
import seaborn as sns
from io import BytesIO
import csv
import os
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score
import numpy as np


# Configuración inicial
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
db = SQLAlchemy(app)

# Asegurar que la carpeta plots exista
os.makedirs('plots', exist_ok=True)

def generate_figure():
    df = pd.read_csv('adicciones_sin_bmi.csv')  # archivo sin bmi
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
    social_support = db.Column(db.String(50))
    therapy_history = db.Column(db.String(50))

inicializado = False
modelo_fumador = None
modelo_tomador = None
encoder_gender = None
encoder_mental = None


@app.before_request
def limpiar_una_vez():
    global inicializado
    if not inicializado:
        db.session.query(Persona).delete()
        db.session.commit()
        inicializado = True

@app.route('/')
def index():
    personas = Persona.query.limit(50).all()
    datos_cargados = len(personas) > 0
    return render_template('index.html', personas=personas, datos_cargados=datos_cargados)

@app.route('/cargar', methods=['POST'])
def cargar_csv():
    file = request.files['file']

    # Verificar que el archivo fue subido y que se llama exactamente "adicciones.csv"
    if file and file.filename == 'adicciones.csv':
        stream = file.stream.read().decode('utf-8').splitlines()
        reader = csv.DictReader(stream)
        for row in reader:
            try:
                persona = Persona(
                    id=int(row['id']),
                    age=int(row['age']),
                    gender=row['gender'],
                    smokes_per_day=int(row['smokes_per_day']),
                    drinks_per_week=int(row['drinks_per_week']),
                    age_started_smoking=int(row['age_started_smoking']),
                    age_started_drinking=int(row['age_started_drinking']),
                    attempts_to_quit_smoking=int(row['attempts_to_quit_smoking']),
                    attempts_to_quit_drinking=int(row['attempts_to_quit_drinking']),
                    has_health_issues=row['has_health_issues'].lower() == 'true',
                    mental_health_status=row['mental_health_status'],
                    social_support=row['social_support'],
                    therapy_history=row['therapy_history']
                )
                db.session.add(persona)
            except Exception as e:
                print(f"Error al procesar fila: {row.get('id', 'sin id')} -> {e}")
        db.session.commit()
        # Agregá al final de cargar_csv():
        global modelo_fumador, modelo_tomador, encoder_gender, encoder_mental
        modelo_fumador, modelo_tomador, encoder_gender, encoder_mental = entrenar_modelos()

        return redirect('/')
    else:
        return "El archivo debe llamarse exactamente 'adicciones.csv'", 400
        

@app.route('/dataset_completo')
def dataset_completo():
    df = pd.read_csv('adicciones.csv')  # Asegurate que esta ruta sea correcta
    tabla_html = df.to_html(classes='table table-bordered table-striped', index=False)
    return render_template('dataset_completo.html', tabla_html=tabla_html)


@app.route('/graficos')
def graficos():
    df = pd.read_sql(db.session.query(Persona).statement, db.engine)
    fig, axes = plt.subplots(5, 2, figsize=(15, 20))
    plt.subplots_adjust(hspace=0.5)

    # Gráficos
    smoker_gender = df[df['smokes_per_day'] > 0]['gender'].value_counts()
    axes[0, 0].pie(smoker_gender, labels=smoker_gender.index, autopct='%1.1f%%', colors=sns.color_palette('pastel'))
    axes[0, 0].set_title('Fumadores por género')

    drinker_gender = df[df['drinks_per_week'] > 0]['gender'].value_counts()
    axes[0, 1].pie(drinker_gender, labels=drinker_gender.index, autopct='%1.1f%%', colors=sns.color_palette('muted'))
    axes[0, 1].set_title('Tomadores por género')

    top_smokers = df.sort_values(by='smokes_per_day', ascending=False).head(10)
    axes[1, 0].plot(top_smokers['id'].astype(str), top_smokers['age'], marker='o')
    axes[1, 0].set_title('Top 10 fumadores vs Edad')
    axes[1, 0].set_xlabel('ID Persona')
    axes[1, 0].set_ylabel('Edad')

    sns.boxplot(x='gender', y='drinks_per_week', data=df, ax=axes[1, 1])
    axes[1, 1].set_title('Alcohol por semana según género')

    sns.boxplot(x='mental_health_status', y='smokes_per_day', data=df, ax=axes[2, 0])
    axes[2, 0].set_title('Cigarrillos por día vs Salud mental')

    sns.histplot(df['age_started_smoking'].dropna(), bins=15, ax=axes[2, 1])
    axes[2, 1].set_title('Edad de inicio al fumar')

    sns.histplot(df['age_started_drinking'].dropna(), bins=15, ax=axes[3, 0])
    axes[3, 0].set_title('Edad de inicio al beber alcohol')

    sns.countplot(x='attempts_to_quit_smoking', data=df, ax=axes[3, 1])
    axes[3, 1].set_title('Intentos de dejar de fumar')

    sns.countplot(x='attempts_to_quit_drinking', data=df, ax=axes[4, 0])
    axes[4, 0].set_title('Intentos de dejar de tomar')

    sns.boxplot(x='social_support', y='smokes_per_day', data=df, ax=axes[4, 1])
    axes[4, 1].set_title('Apoyo social vs Cigarrillos por día')

    plt.savefig('plots/graficos.png')
    plt.close()

    with open("plots/graficos.png", "rb") as image_file:
        plot_url = base64.b64encode(image_file.read()).decode()

    return render_template('graficos.html', plot_url=plot_url)

@app.route('/analisis_de_datos')
def analisis_de_datos():
    df = pd.read_sql(db.session.query(Persona).statement, db.engine)

    estadisticas = {
        'Edad promedio': round(df['age'].mean(), 2),
        'Edad máxima': df['age'].max(),
        'Edad mínima': df['age'].min(),
        'Cigarrillos promedio': round(df['smokes_per_day'].mean(), 2),
        'Alcohol promedio': round(df['drinks_per_week'].mean(), 2),
    }

    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    plt.subplots_adjust(hspace=0.4)

    sns.histplot(df['age'], bins=20, kde=True, ax=axes[0, 0], color='skyblue')
    axes[0, 0].set_title('Distribución de Edad')

    sns.boxplot(x='smokes_per_day', data=df, ax=axes[0, 1], color='lightcoral')
    axes[0, 1].set_title('Distribución de Cigarrillos por Día')

    sns.histplot(df['drinks_per_week'], bins=20, kde=True, ax=axes[1, 0], color='lightgreen')
    axes[1, 0].set_title('Distribución de Consumo de Alcohol por Semana')

    sns.regplot(x='age', y='smokes_per_day', data=df, ax=axes[1, 1], scatter_kws={'alpha':0.5})
    axes[1, 1].set_title('Edad vs Cigarrillos por Día')

    plt.tight_layout()
    plt.savefig('plots/analisis.png')
    plt.close()

    with open("plots/analisis.png", "rb") as image_file:
        plot_url = base64.b64encode(image_file.read()).decode()

    resumen_tabla = df[['age', 'smokes_per_day', 'drinks_per_week']].describe().round(2).to_html(classes="table table-striped")

    return render_template('analisis_de_datos.html', plot_url=plot_url, resumen_tabla=resumen_tabla, estadisticas=estadisticas)


def entrenar_modelos():
    df = pd.read_sql(db.session.query(Persona).statement, db.engine)

    if df.empty:
        print("⚠️ No hay datos para entrenar los modelos.")
        return None, None, None, None

    # Variables objetivo
    df['es_fumador_frecuente'] = df['smokes_per_day'] > 10
    df['es_tomador_frecuente'] = df['drinks_per_week'] > 7  # umbral ejemplo

    # Variables seleccionadas
    features = ['age', 'gender', 'smokes_per_day', 'age_started_smoking',
                'attempts_to_quit_smoking', 'has_health_issues', 'mental_health_status']

    X_fumador = df[features].copy()
    y_fumador = df['es_fumador_frecuente'].astype(int)

    # Para tomador, puedes usar las mismas variables menos smokes_per_day (porque es para fumar)
    features_tomador = ['age', 'gender', 'smokes_per_day', 'age_started_drinking',
                       'attempts_to_quit_drinking', 'has_health_issues', 'mental_health_status']
    X_tomador = df[features_tomador].copy()
    y_tomador = df['es_tomador_frecuente'].astype(int)

    # Codificar variables categóricas (mismo encoder para consistencia)
    le_gender = LabelEncoder()
    X_fumador['gender'] = le_gender.fit_transform(X_fumador['gender'])
    X_tomador['gender'] = le_gender.transform(X_tomador['gender'])

    le_mental = LabelEncoder()
    X_fumador['mental_health_status'] = le_mental.fit_transform(X_fumador['mental_health_status'])
    X_tomador['mental_health_status'] = le_mental.transform(X_tomador['mental_health_status'])

    # Codificar booleanos (has_health_issues)
    X_fumador['has_health_issues'] = X_fumador['has_health_issues'].astype(int)
    X_tomador['has_health_issues'] = X_tomador['has_health_issues'].astype(int)

    # Entrenar modelos
    modelo_fumador = LogisticRegression(max_iter=1000)
    modelo_fumador.fit(X_fumador, y_fumador)

    modelo_tomador = LogisticRegression(max_iter=1000)
    modelo_tomador.fit(X_tomador, y_tomador)

    return modelo_fumador, modelo_tomador, le_gender, le_mental

# Entrena ambos modelos dentro del contexto Flask para evitar errores con db.session

@app.route('/predict', methods=['GET', 'POST'])
def predict():
    if modelo_fumador is None or modelo_tomador is None:
        return "Modelos no disponibles. Cargá el archivo CSV primero desde la página principal.", 400
    if request.method == 'POST':
        try:
            age = int(request.form['age'])
            gender = request.form['gender']
            smokes_per_day = int(request.form['smokes_per_day'])
            drinks_per_week = int(request.form['drinks_per_week'])
            age_started_smoking = int(request.form['age_started_smoking'])
            age_started_drinking = int(request.form['age_started_drinking'])
            attempts_to_quit_smoking = int(request.form['attempts_to_quit_smoking'])
            attempts_to_quit_drinking = int(request.form['attempts_to_quit_drinking'])
            has_health_issues = request.form['has_health_issues'] == 'true'
            mental_health_status = request.form['mental_health_status']

            gender_encoded = encoder_gender.transform([gender])[0]
            mental_encoded = encoder_mental.transform([mental_health_status])[0]

            # Datos para modelo de fumador
            input_fumador = np.array([[age, gender_encoded, smokes_per_day,
                                    age_started_smoking, attempts_to_quit_smoking,
                                    int(has_health_issues), mental_encoded]])

            # Datos para modelo de tomador
            input_tomador = np.array([[age, gender_encoded, smokes_per_day,
                                      age_started_drinking, attempts_to_quit_drinking,
                                      int(has_health_issues), mental_encoded]])

            prob_fumador = modelo_fumador.predict_proba(input_fumador)[0][1]
            prob_tomador = modelo_tomador.predict_proba(input_tomador)[0][1]

            return render_template('predict_result.html',
                                   prob_fumador=round(prob_fumador * 100, 2),
                                   prob_tomador=round(prob_tomador * 100, 2))

        except Exception as e:
            return f"Error en predicción: {e}"

    return render_template('predict_form.html')
    

if __name__ == "__main__":
    app.run(debug=True)
