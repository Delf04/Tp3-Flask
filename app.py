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


os.makedirs('plots', exist_ok=True)

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
        db.create_all()
        db.session.query(Persona).delete()
        db.session.commit()
        inicializado = True

@app.route('/')
def index(limit=15):
    personas = Persona.query.limit(limit).all()
    datos_cargados = len(personas) > 0
    return render_template('index.html', personas=personas, datos_cargados=datos_cargados)

@app.route('/cargar', methods=['POST'])
def cargar_csv():
    file = request.files['file']
    if file and file.filename == 'adicciones.csv':
        stream = file.stream.read().decode('utf-8').splitlines()
        reader = csv.DictReader(stream)
        personas_a_agregar = []
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
                personas_a_agregar.append(persona)
            except Exception as e:
                print(f"Error al procesar fila: {row.get('id', 'sin id')} -> {e}")

        # Inserta todas las personas en una sola transacción
        db.session.bulk_save_objects(personas_a_agregar)
        db.session.commit()

        global modelo_fumador, modelo_tomador, encoder_gender, encoder_mental
        modelo_fumador, modelo_tomador, encoder_gender, encoder_mental = entrenar_modelos()

        return redirect('/')
    else:
        return "El archivo debe llamarse exactamente 'adicciones.csv'", 400        

@app.route('/dataset_completo')
def dataset_completo():
    df = pd.read_csv('adicciones.csv')  
    tabla_html = df.to_html(classes='table table-bordered table-striped', index=False)
    return render_template('dataset_completo.html', tabla_html=tabla_html)



# Ruta para gráficos
@app.route('/graficos')
def graficos():
    df = pd.read_sql(db.session.query(Persona).statement, db.engine)
    plot_dir = 'plots'
    os.makedirs(plot_dir, exist_ok=True)
    plot_files = []

    # 1. Edad de inicio al fumar
    fig1, ax1 = plt.subplots(figsize=(6, 4))
    sns.histplot(df['age_started_smoking'].dropna(), bins=15, ax=ax1, color='orange')
    ax1.set_title('Edad de inicio al fumar')
    file1 = os.path.join(plot_dir, 'edad_inicio_fumar.png')
    fig1.savefig(file1)
    plt.close(fig1)
    plot_files.append(file1)

    # 2. Edad de inicio al beber alcohol
    fig2, ax2 = plt.subplots(figsize=(6, 4))
    sns.histplot(df['age_started_drinking'].dropna(), bins=15, ax=ax2, color='green')
    ax2.set_title('Edad de inicio al beber alcohol')
    file2 = os.path.join(plot_dir, 'edad_inicio_beber.png')
    fig2.savefig(file2)
    plt.close(fig2)
    plot_files.append(file2)

    # 3. Intentos de dejar de tomar
    fig3, ax3 = plt.subplots(figsize=(6, 4))
    sns.countplot(x='attempts_to_quit_drinking', data=df, ax=ax3, palette='Purples')
    ax3.set_title('Intentos de dejar de tomar')
    file3 = os.path.join(plot_dir, 'intentos_dejar_tomar.png')
    fig3.savefig(file3)
    plt.close(fig3)
    plot_files.append(file3)

    # 4. Distribución de género
    fig4, ax4 = plt.subplots(figsize=(6, 4))
    sns.countplot(x='gender', data=df, ax=ax4, palette='Set2')
    ax4.set_title('Distribución de Género')
    file4 = os.path.join(plot_dir, 'distribucion_genero.png')
    fig4.savefig(file4)
    plt.close(fig4)
    plot_files.append(file4)

    # 5. Relación entre edad y consumo de alcohol
    fig5, ax5 = plt.subplots(figsize=(6, 4))
    sns.scatterplot(x='age', y='drinks_per_week', data=df, ax=ax5, alpha=0.6)
    ax5.set_title('Edad vs Consumo de Alcohol por Semana')
    file5 = os.path.join(plot_dir, 'edad_vs_alcohol.png')
    fig5.savefig(file5)
    plt.close(fig5)
    plot_files.append(file5)

    # 6. Distribución de personas con problemas de salud
    fig6, ax6 = plt.subplots(figsize=(6, 4))
    sns.countplot(x='has_health_issues', data=df, ax=ax6, palette='Set1')
    ax6.set_title('Distribución de Problemas de Salud')
    file6 = os.path.join(plot_dir, 'distribucion_salud.png')
    fig6.savefig(file6)
    plt.close(fig6)
    plot_files.append(file6)

    # 7. Relación entre cigarrillos y alcohol
    fig7, ax7 = plt.subplots(figsize=(6, 4))
    sns.scatterplot(x='smokes_per_day', y='drinks_per_week', data=df, ax=ax7, alpha=0.6)
    ax7.set_title('Cigarrillos por día vs Alcohol por semana')
    file7 = os.path.join(plot_dir, 'cigarrillos_vs_alcohol.png')
    fig7.savefig(file7)
    plt.close(fig7)
    plot_files.append(file7)

    # Codificar imágenes en base64 para mostrar en la plantilla
    plot_urls = []
    for file in plot_files:
        with open(file, "rb") as image_file:
            plot_urls.append(base64.b64encode(image_file.read()).decode())

    return render_template('graficos.html', plot_urls=plot_urls)


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

    plot_dir = 'plots'
    os.makedirs(plot_dir, exist_ok=True)
    plot_files = []  # Acá almacenamos todas las imágenes

    # 1. Relación entre edad de inicio de fumar y cigarrillos por día
    file1 = os.path.join(plot_dir, 'edad_inicio_fumar_vs_cigarrillos.png')
    fig1, ax1 = plt.subplots(figsize=(6, 4))
    sns.scatterplot(
        x='age_started_smoking', y='smokes_per_day', data=df, ax=ax1, alpha=0.6, color='teal'
    )
    ax1.set_title('Edad de inicio de fumar vs Cigarrillos por día')
    fig1.tight_layout()
    fig1.savefig(file1)
    plt.close(fig1)
    plot_files.append(file1)

    # 2. Relación entre edad de inicio de beber y consumo de alcohol semanal
    file2 = os.path.join(plot_dir, 'edad_inicio_beber_vs_alcohol.png')
    fig2, ax2 = plt.subplots(figsize=(6, 4))
    sns.scatterplot(
        x='age_started_drinking', y='drinks_per_week', data=df, ax=ax2, alpha=0.6, color='purple'
    )
    ax2.set_title('Edad de inicio de beber vs Alcohol por semana')
    fig2.tight_layout()
    fig2.savefig(file2)
    plt.close(fig2)
    plot_files.append(file2)

    # 3. Boxplot de intentos de dejar de fumar según apoyo social
    file3 = os.path.join(plot_dir, 'intentos_dejar_fumar_vs_apoyo_social.png')
    fig3, ax3 = plt.subplots(figsize=(6, 4))
    sns.boxplot(
        x='social_support', y='attempts_to_quit_smoking', data=df, ax=ax3, palette='pastel'
    )
    ax3.set_title('Intentos de dejar de fumar según Apoyo Social')
    ax3.tick_params(axis='x', rotation=30)
    fig3.tight_layout()
    fig3.savefig(file3)
    plt.close(fig3)
    plot_files.append(file3)

    # Codificar imágenes en base64 para mostrar en la plantilla
    plot_urls = []
    for file in plot_files:
        with open(file, "rb") as image_file:
            plot_urls.append(base64.b64encode(image_file.read()).decode())

    resumen_tabla = df[['age', 'smokes_per_day', 'drinks_per_week']].describe().round(2).to_html(classes="table table-striped")

    return render_template(
        'analisis_de_datos.html',
        plot_urls=plot_urls,
        resumen_tabla=resumen_tabla,
        estadisticas=estadisticas
    )



def entrenar_modelos():
    df = pd.read_sql(db.session.query(Persona).statement, db.engine)

    if df.empty:
        print("No hay datos para entrenar los modelos.")
        return None, None, None, None

    # Variables objetivo
    df['es_fumador_frecuente'] = df['smokes_per_day'] > 10
    df['es_tomador_frecuente'] = df['drinks_per_week'] > 7  

    # Variables seleccionadas
    features = ['age', 'gender', 'smokes_per_day', 'age_started_smoking',
                'attempts_to_quit_smoking', 'has_health_issues', 'mental_health_status']

    X_fumador = df[features].copy()
    y_fumador = df['es_fumador_frecuente'].astype(int)

    features_tomador = ['age', 'gender', 'smokes_per_day', 'age_started_drinking',
                       'attempts_to_quit_drinking', 'has_health_issues', 'mental_health_status']
    X_tomador = df[features_tomador].copy()
    y_tomador = df['es_tomador_frecuente'].astype(int)

    le_gender = LabelEncoder()
    X_fumador['gender'] = le_gender.fit_transform(X_fumador['gender'])
    X_tomador['gender'] = le_gender.transform(X_tomador['gender'])

    le_mental = LabelEncoder()
    X_fumador['mental_health_status'] = le_mental.fit_transform(X_fumador['mental_health_status'])
    X_tomador['mental_health_status'] = le_mental.transform(X_tomador['mental_health_status'])

    X_fumador['has_health_issues'] = X_fumador['has_health_issues'].astype(int)
    X_tomador['has_health_issues'] = X_tomador['has_health_issues'].astype(int)

    modelo_fumador = LogisticRegression(max_iter=1000)
    modelo_fumador.fit(X_fumador, y_fumador)

    modelo_tomador = LogisticRegression(max_iter=1000)
    modelo_tomador.fit(X_tomador, y_tomador)

    return modelo_fumador, modelo_tomador, le_gender, le_mental



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

            return render_template('resultado_prediccion.html',
                                   prob_fumador=round(prob_fumador * 100, 2),
                                   prob_tomador=round(prob_tomador * 100, 2))

        except Exception as e:
            return f"Error en predicción: {e}"

    return render_template('form_prediccion.html')
    

if __name__ == "__main__":
    app.run(debug=True)

