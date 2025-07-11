from flask import Flask, render_template, request, redirect
from models import db, Persona
from utils.helpers import procesar_csv, leer_dataset, codificar_imagenes, entrenar_modelos
from utils.plots import generar_graficos_generales, generar_graficos_analisis, DESCRIPCIONES_ANALISIS, DESCRIPCIONES_GRAFICOS
import os
import pandas as pd
from flask import url_for

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
db.init_app(app)

os.makedirs('plots', exist_ok=True)
inicializado = False
modelos = {}

@app.before_request
def inicializar():
    global inicializado
    if not inicializado:
        with app.app_context():
            db.create_all()
            db.session.query(Persona).delete()
            db.session.commit()
        inicializado = True



@app.route('/')
def index():
    personas = Persona.query.limit(15).all()
    return render_template('index.html', personas=personas, datos_cargados=len(personas) > 0)



@app.route('/cargar', methods=['POST'])
def cargar_csv():
    file = request.files['file']
    if file and file.filename == 'adicciones.csv':
        procesar_csv(file)  
        global modelos
        modelos = entrenar_modelos()
        return redirect('/')
    return "El archivo debe llamarse exactamente 'adicciones.csv'", 



@app.route('/dataset_completo', methods=['GET', 'POST'])
def dataset_completo():
    df = pd.read_csv('adicciones.csv')  

    if df.empty:
        return "No hay datos disponibles. Subí el CSV desde la página principal.", 400

    generos = sorted(df['gender'].dropna().unique())
    estados_civiles = sorted(df['marital_status'].dropna().unique())
    salud_mental = sorted(df['mental_health_status'].dropna().unique())
    educaciones = sorted(df['education_level'].dropna().unique())
    empleos = sorted(df['employment_status'].dropna().unique())

    df_filtrado = df.copy()
    edad_min = 0
    edad_max = 100
    genero = 'Todos'
    estado_civil = 'Todos'
    fumador = ''
    bebedor = ''
    mental = 'Todos'
    educacion = 'Todos'
    empleo = 'Todos'
    salud = ''

    if request.method == 'POST':
        edad_min = max(0, min(int(request.form.get('edad_min', 0)), 80))
        edad_max = max(0, min(int(request.form.get('edad_max', 80)), 80))
        genero = request.form.get('genero')
        estado_civil = request.form.get('estado_civil')
        fumador = request.form.get('fumador')
        bebedor = request.form.get('bebedor')
        mental = request.form.get('salud_mental')
        educacion = request.form.get('educacion')
        empleo = request.form.get('empleo')
        salud = request.form.get('salud')

        df_filtrado = df_filtrado[
            (df_filtrado['age'] >= edad_min) & (df_filtrado['age'] <= edad_max)
        ]

        if genero and genero != 'Todos':
            df_filtrado = df_filtrado[df_filtrado['gender'] == genero]

        if estado_civil and estado_civil != 'Todos':
            df_filtrado = df_filtrado[df_filtrado['marital_status'] == estado_civil]

        if fumador == 'sí':
            df_filtrado = df_filtrado[df_filtrado['smokes_per_day'] > 10]
        elif fumador == 'no':
            df_filtrado = df_filtrado[df_filtrado['smokes_per_day'] <= 10]

        if bebedor == 'sí':
            df_filtrado = df_filtrado[df_filtrado['drinks_per_week'] > 7]
        elif bebedor == 'no':
            df_filtrado = df_filtrado[df_filtrado['drinks_per_week'] <= 7]

        if mental and mental != 'Todos':
            df_filtrado = df_filtrado[df_filtrado['mental_health_status'] == mental]

        if educacion and educacion != 'Todos':
            df_filtrado = df_filtrado[df_filtrado['education_level'] == educacion]

        if empleo and empleo != 'Todos':
            df_filtrado = df_filtrado[df_filtrado['employment_status'] == empleo]

        if salud == 'sí':
            df_filtrado = df_filtrado[df_filtrado['has_health_issues'] == True]
        elif salud == 'no':
            df_filtrado = df_filtrado[df_filtrado['has_health_issues'] == False]

    tabla_filtrada = df_filtrado.round(2).to_html(classes="table table-bordered table-striped", index=False)
    tabla_completa = df.round(2).to_html(classes="table table-bordered table-striped", index=False)
    return render_template(
        'dataset_completo.html',
        generos=generos,
        estados_civiles=estados_civiles,
        salud_mental=salud_mental,
        educaciones=educaciones,
        empleos=empleos,
        tabla_filtrada=tabla_filtrada,
        tabla_completa=tabla_completa,
        edad_min=edad_min,
        edad_max=edad_max,
        genero=genero,
        estado_civil=estado_civil,
        fumador=fumador,
        bebedor=bebedor,
        mental=mental,
        educacion=educacion,
        empleo=empleo,
        salud=salud
    )



@app.route("/graficos")
def graficos():
    df = leer_dataset()
    if df.empty:
        return render_template("graficos.html", plot_urls=[])

    output_dir = "static/graficos"
    plot_files = generar_graficos_generales(df, output_dir)
    plot_urls = codificar_imagenes(plot_files, DESCRIPCIONES_GRAFICOS) 
    return render_template("graficos.html", plot_urls=plot_urls)


@app.route('/analisis_de_datos')
def analisis_de_datos():
    df = leer_dataset()  # Cargar siempre

    estadisticas = {
        'Edad promedio': round(df['age'].mean(), 2),
        'Edad máxima': df['age'].max(),
        'Edad mínima': df['age'].min(),
        'Cigarrillos promedio': round(df['smokes_per_day'].mean(), 2),
        'Alcohol promedio': round(df['drinks_per_week'].mean(), 2),
    }

    plot_files = generar_graficos_analisis(df, 'static/graficos')

    plot_urls = [
        {'url': url_for('static', filename=f"graficos/{os.path.basename(f)}"), 
         'descripcion': DESCRIPCIONES_ANALISIS.get(os.path.basename(f), '')}
        for f in plot_files
    ]
    resumen_tabla = df[['age', 'smokes_per_day', 'drinks_per_week']].describe().round(2).to_html(classes="table table-striped")
    return render_template('analisis_de_datos.html', plot_urls=plot_urls, resumen_tabla=resumen_tabla, estadisticas=estadisticas)




@app.route('/predict', methods=['GET', 'POST'])
def predict():
    if not modelos:
        return "Modelos no disponibles. Cargá el archivo CSV primero desde la página principal.", 400

    if request.method == 'POST':
        try:
            datos = {
                'age': request.form['age'],
                'gender': request.form['gender'],
                'smokes_per_day': request.form['smokes_per_day'],
                'drinks_per_week': request.form['drinks_per_week'],
                'age_started_smoking': request.form['age_started_smoking'],
                'age_started_drinking': request.form['age_started_drinking'],
                'attempts_to_quit_smoking': request.form['attempts_to_quit_smoking'],
                'attempts_to_quit_drinking': request.form['attempts_to_quit_drinking'],
                'has_health_issues': request.form['has_health_issues'],
                'mental_health_status': request.form['mental_health_status'],
                'social_support': request.form['social_support'],
                'therapy_history': request.form['therapy_history'],
                'education_level': request.form['education_level'],
                'employment_status': request.form['employment_status'],
                'annual_income_usd': request.form['annual_income_usd'],
                'marital_status': request.form['marital_status'],
                'children_count': request.form['children_count'],
                'exercise_frequency': request.form['exercise_frequency'],
                'diet_quality': request.form['diet_quality'],
                'sleep_hours': request.form['sleep_hours'],
                'bmi': request.form['bmi']
            }

            resultado = modelos['predecir'](datos)
            return render_template('resultado_prediccion.html', **resultado)

        except Exception as e:
            return f"Error en predicción: {e}", 500

    return render_template('form_prediccion.html')




if __name__ == '__main__':
    app.run(debug=True)