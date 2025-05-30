from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import base64
from io import BytesIO
import csv

# Configuración inicial
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


# Carga de CSV
@app.route('/cargar', methods=['POST'])
def cargar_csv():
    file = request.files['file']
    if file and file.filename.endswith('.csv'):
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
                    bmi=float(row['bmi']),
                    social_support=row['social_support'],
                    therapy_history=row['therapy_history']
                )
                db.session.add(persona)
            except Exception as e:
                print(f"Error al procesar fila: {row['id']} -> {e}")
        db.session.commit()
        return redirect('/')
    return "Archivo no válido", 400


# Ruta para gráficos
@app.route('/graficos')
def graficos():
    df = pd.read_sql(db.session.query(Persona).statement, db.engine)

    fig, axes = plt.subplots(6, 2, figsize=(18, 24))
    plt.subplots_adjust(hspace=0.4)

    # 1. Pie chart fumadores por género
    smoker_gender = df[df['smokes_per_day'] > 0]['gender'].value_counts()
    axes[0, 0].pie(smoker_gender, labels=smoker_gender.index, autopct='%1.1f%%', colors=sns.color_palette('pastel'))
    axes[0, 0].set_title('Fumadores por género')

    # 2. Pie chart tomadores por género
    drinker_gender = df[df['drinks_per_week'] > 0]['gender'].value_counts()
    axes[0, 1].pie(drinker_gender, labels=drinker_gender.index, autopct='%1.1f%%', colors=sns.color_palette('muted'))
    axes[0, 1].set_title('Tomadores por género')

    # 3. Line chart top 10 que más fuman vs edad
    top_smokers = df.sort_values(by='smokes_per_day', ascending=False).head(10)
    axes[1, 0].plot(top_smokers['id'].astype(str), top_smokers['age'], marker='o')
    axes[1, 0].set_title('Top 10 fumadores vs Edad')
    axes[1, 0].set_xlabel('ID Persona')
    axes[1, 0].set_ylabel('Edad')

    # 4. Boxplot consumo de alcohol por género
    sns.boxplot(x='gender', y='drinks_per_week', data=df, ax=axes[1, 1])
    axes[1, 1].set_title('Alcohol por semana según género')

    # 5. Displot IMC
    sns.histplot(df['bmi'], bins=20, kde=True, ax=axes[2, 0], color='orange')
    axes[2, 0].set_title('Distribución del IMC')

    # 6. Consumo de cigarrillos por estado de salud mental
    sns.boxplot(x='mental_health_status', y='smokes_per_day', data=df, ax=axes[2, 1])
    axes[2, 1].set_title('Cigarrillos por día vs Salud mental')

    # 7. Displot edad de inicio del cigarro
    sns.histplot(df['age_started_smoking'].dropna(), bins=15, ax=axes[3, 0])
    axes[3, 0].set_title('Edad de inicio al fumar')

    # 8. Displot edad de inicio del alcohol
    sns.histplot(df['age_started_drinking'].dropna(), bins=15, ax=axes[3, 1])
    axes[3, 1].set_title('Edad de inicio al beber alcohol')

    # 9. Intentos de dejar de fumar
    sns.countplot(x='attempts_to_quit_smoking', data=df, ax=axes[4, 0])
    axes[4, 0].set_title('Intentos de dejar de fumar')

    # 10. Intentos de dejar de tomar
    sns.countplot(x='attempts_to_quit_drinking', data=df, ax=axes[4, 1])
    axes[4, 1].set_title('Intentos de dejar de tomar')

    # 11. Apoyo social vs consumo cigarrillos
    sns.boxplot(x='social_support', y='smokes_per_day', data=df, ax=axes[5, 0])
    axes[5, 0].set_title('Apoyo social vs Cigarrillos por día')

    # 12. Histograma de horas de sueño (si estuviera en tu modelo)
    # Si no tenés esa columna, podés cambiar este gráfico por otro útil
    if 'sleep_hours' in df.columns:
        sns.histplot(df['sleep_hours'], bins=10, ax=axes[5, 1])
        axes[5, 1].set_title('Horas de sueño')
    else:
        axes[5, 1].axis('off')

    # Guardar imagen
    img = BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    alcohol_img = base64.b64encode(img.getvalue()).decode()

    return render_template('graficos.html', plot_url=plot_url)

# Ruta para análisis
@app.route('/analisis_de_datos')
def analisis_de_datos():
    df = pd.read_sql(db.session.query(Persona).statement, db.engine)

    # Estadísticas básicas (pueden usarse para títulos o info adicional)
    estadisticas = {
        'Edad promedio': round(df['age'].mean(), 2),
        'Edad máxima': df['age'].max(),
        'Edad mínima': df['age'].min(),
        'Cigarrillos promedio': round(df['smokes_per_day'].mean(), 2),
        'Alcohol promedio': round(df['drinks_per_week'].mean(), 2),
        'IMC promedio': round(df['bmi'].mean(), 2),
        'IMC máximo': df['bmi'].max(),
        'IMC mínimo': df['bmi'].min(),
    }

    # Creamos una figura con varios gráficos
    fig, axes = plt.subplots(3, 2, figsize=(14, 12))
    plt.subplots_adjust(hspace=0.4)

    # 1. Histograma de edades
    sns.histplot(df['age'], bins=20, kde=True, ax=axes[0, 0], color='skyblue')
    axes[0, 0].set_title('Distribución de Edad')

    # 2. Boxplot cigarrillos por día
    sns.boxplot(x='smokes_per_day', data=df, ax=axes[0, 1], color='lightcoral')
    axes[0, 1].set_title('Distribución de Cigarrillos por Día')

    # 3. Histograma consumo alcohol por semana
    sns.histplot(df['drinks_per_week'], bins=20, kde=True, ax=axes[1, 0], color='lightgreen')
    axes[1, 0].set_title('Distribución de Consumo de Alcohol por Semana')

    # 4. Boxplot IMC
    sns.boxplot(x='bmi', data=df, ax=axes[1, 1], color='orange')
    axes[1, 1].set_title('Distribución de IMC')

    # 5. Scatter plot Edad vs Cigarrillos (con regresión)
    sns.regplot(x='age', y='smokes_per_day', data=df, ax=axes[2, 0], scatter_kws={'alpha':0.5})
    axes[2, 0].set_title('Edad vs Cigarrillos por Día')

    # 6. Scatter plot IMC vs Alcohol (con regresión)
    sns.regplot(x='bmi', y='drinks_per_week', data=df, ax=axes[2, 1], scatter_kws={'alpha':0.5}, color='purple')
    axes[2, 1].set_title('IMC vs Consumo de Alcohol por Semana')

    # Guardar la imagen en memoria
    img = BytesIO()
    plt.tight_layout()
    plt.savefig(img, format='png')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode()
    plt.close()

    # Tabla estadística (describe) para mostrar en HTML
    resumen_tabla = df[['age', 'smokes_per_day', 'drinks_per_week', 'bmi']].describe().round(2).to_html(classes="table table-striped")

    return render_template('analisis_de_datos.html', plot_url=plot_url, resumen_tabla=resumen_tabla, estadisticas=estadisticas)


# Main
if __name__ == "__main__":
    app.run(debug=True)
