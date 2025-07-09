from flask import Flask, render_template, request, redirect
from models import db, Persona
from utils.helpers import procesar_csv, leer_dataset, codificar_imagenes, entrenar_modelos
from utils.plots import generar_graficos_generales, generar_graficos_analisis, DESCRIPCIONES_ANALISIS, DESCRIPCIONES_GRAFICOS
from utils.helpers import filtrar_dataset
import os
import pandas as pd

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
    if request.method == 'POST':
        df, df_filtrado, opciones, filtros = filtrar_dataset(request.form)
    else:
        df, df_filtrado, opciones, filtros = filtrar_dataset()

    if df is None:
        return "No hay datos disponibles. Subí el CSV desde la página principal.", 400

    tabla_filtrada = df_filtrado.round(2).to_html(classes="table table-bordered table-striped", index=False)
    tabla_completa = df.round(2).to_html(classes="table table-bordered table-striped", index=False)

    # Agregar conteos de registros
    total_registros = len(df)
    registros_filtrados = len(df_filtrado)

    template_vars = {
        'tabla_filtrada': tabla_filtrada,
        'tabla_completa': tabla_completa,
        'rangos': opciones['rangos'],
        'categorias': opciones['categorias'],
        'filtros': filtros,
        'total_registros': total_registros,
        'registros_filtrados': registros_filtrados
    }

    return render_template('dataset_completo.html', **template_vars)




@app.route("/graficos")
def graficos():
    df = leer_dataset()
    if df.empty:
        return render_template("graficos.html", plot_urls=[])

    output_dir = "static/graficos"
    plot_files = generar_graficos_generales(df, output_dir)
    plot_urls = codificar_imagenes(plot_files, DESCRIPCIONES_GRAFICOS)  # <-- Aquí el diccionario ANALISIS
    return render_template("graficos.html", plot_urls=plot_urls)


@app.route('/analisis_de_datos')
def analisis_de_datos():
    df = leer_dataset()
    estadisticas = {
        'Edad promedio': round(df['age'].mean(), 2),
        'Edad máxima': df['age'].max(),
        'Edad mínima': df['age'].min(),
        'Cigarrillos promedio': round(df['smokes_per_day'].mean(), 2),
        'Alcohol promedio': round(df['drinks_per_week'].mean(), 2),
    }
    plot_files = generar_graficos_analisis(df, 'plots')
    plot_urls = codificar_imagenes(plot_files, DESCRIPCIONES_ANALISIS) 
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