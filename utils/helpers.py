import pandas as pd
import numpy as np
import base64
import csv
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import LabelEncoder
from models import db, Persona

def procesar_csv(file):
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
                therapy_history=row['therapy_history'],
                education_level=row.get('education_level', None),
                employment_status=row.get('employment_status', None),
                annual_income_usd=int(row['annual_income_usd']) if row.get('annual_income_usd') else None,
                marital_status=row.get('marital_status', None),
                children_count=int(row['children_count']) if row.get('children_count') else None,
                exercise_frequency=row.get('exercise_frequency', None),
                diet_quality=row.get('diet_quality', None),
                sleep_hours=float(row['sleep_hours']) if row.get('sleep_hours') else None,
                bmi=float(row['bmi']) if row.get('bmi') else None
            )
            personas_a_agregar.append(persona)
        except Exception as e:
            print(f"Error al procesar fila: {row.get('id', 'sin id')} -> {e}")

    db.session.bulk_save_objects(personas_a_agregar)
    db.session.commit()


def leer_dataset():
    return pd.read_sql(db.session.query(Persona).statement, db.engine)

def codificar_imagenes(plot_files):
    urls = []
    for file in plot_files:
        with open(file, "rb") as f:
            urls.append(base64.b64encode(f.read()).decode())
    return urls

def entrenar_modelos():
    df = leer_dataset()
    if df.empty:
        return {}

    # Variables objetivo
    df['es_fumador_frecuente'] = df['smokes_per_day'] > 10
    df['es_tomador_frecuente'] = df['drinks_per_week'] > 7

    # Valores posibles para forzar codificadores robustos
    valores_posibles = {
        'gender': ['Male', 'Female', 'Other'],
        'mental_health_status': ['Good', 'Average', 'Poor'],
        'social_support': ['High', 'Moderate', 'Low'],
        'therapy_history': ['Yes', 'No'],
        'education_level': ['Primary', 'Secondary', 'Tertiary', 'University', 'Postgraduate'],
        'employment_status': ['Employed', 'Unemployed', 'Student', 'Retired'],
        'marital_status': ['Single', 'Married', 'Divorced', 'Widowed'],
        'exercise_frequency': ['Never', 'Sometimes', 'Regular'],
        'diet_quality': ['Poor', 'Average', 'Good']
    }

    for var, valores in valores_posibles.items():
        for valor in valores:
            if valor not in df[var].values:
                dummy = df.iloc[0].copy()
                dummy[var] = valor
                df = df._append(dummy, ignore_index=True)

    # Variables a usar en los modelos
    features = [
        'age', 'gender', 'smokes_per_day', 'age_started_smoking',
        'attempts_to_quit_smoking', 'has_health_issues', 'mental_health_status',
        'social_support', 'therapy_history', 'education_level', 'employment_status',
        'annual_income_usd', 'marital_status', 'children_count', 'exercise_frequency',
        'diet_quality', 'sleep_hours', 'bmi'
    ]

    features_tomador = [
        'age', 'gender', 'smokes_per_day', 'age_started_drinking',
        'attempts_to_quit_drinking', 'has_health_issues', 'mental_health_status',
        'social_support', 'therapy_history', 'education_level', 'employment_status',
        'annual_income_usd', 'marital_status', 'children_count', 'exercise_frequency',
        'diet_quality', 'sleep_hours', 'bmi'
    ]

    # Separación de datos
    X_fumador = df[features].copy()
    y_fumador = df['es_fumador_frecuente'].astype(int)
    X_tomador = df[features_tomador].copy()
    y_tomador = df['es_tomador_frecuente'].astype(int)

    # Codificadores para variables categóricas
    encoders = {}
    cat_vars = list(valores_posibles.keys())

    for var in cat_vars:
        le = LabelEncoder()
        X_fumador[var] = le.fit_transform(X_fumador[var])
        X_tomador[var] = le.transform(X_tomador[var])
        encoders[var] = le

    # Variables booleanas a entero
    X_fumador['has_health_issues'] = X_fumador['has_health_issues'].astype(int)
    X_tomador['has_health_issues'] = X_tomador['has_health_issues'].astype(int)

    # Entrenamiento
    modelo_fumador = LogisticRegression(max_iter=1000).fit(X_fumador, y_fumador)
    modelo_tomador = LogisticRegression(max_iter=1000).fit(X_tomador, y_tomador)

    # Función de predicción
    def predecir(input_dict):
        def encode(var):
            return encoders[var].transform([input_dict[var]])[0]

        has_health_issues = input_dict['has_health_issues'] == 'true'

        input_fumador = np.array([[int(input_dict['age']),
                                   encode('gender'),
                                   int(input_dict['smokes_per_day']),
                                   int(input_dict['age_started_smoking']),
                                   int(input_dict['attempts_to_quit_smoking']),
                                   int(has_health_issues),
                                   encode('mental_health_status'),
                                   encode('social_support'),
                                   encode('therapy_history'),
                                   encode('education_level'),
                                   encode('employment_status'),
                                   int(input_dict['annual_income_usd']),
                                   encode('marital_status'),
                                   int(input_dict['children_count']),
                                   encode('exercise_frequency'),
                                   encode('diet_quality'),
                                   float(input_dict['sleep_hours']),
                                   float(input_dict['bmi'])]])

        input_tomador = np.array([[int(input_dict['age']),
                                   encode('gender'),
                                   int(input_dict['smokes_per_day']),
                                   int(input_dict['age_started_drinking']),
                                   int(input_dict['attempts_to_quit_drinking']),
                                   int(has_health_issues),
                                   encode('mental_health_status'),
                                   encode('social_support'),
                                   encode('therapy_history'),
                                   encode('education_level'),
                                   encode('employment_status'),
                                   int(input_dict['annual_income_usd']),
                                   encode('marital_status'),
                                   int(input_dict['children_count']),
                                   encode('exercise_frequency'),
                                   encode('diet_quality'),
                                   float(input_dict['sleep_hours']),
                                   float(input_dict['bmi'])]])

        prob_fumador = modelo_fumador.predict_proba(input_fumador)[0][1]
        prob_tomador = modelo_tomador.predict_proba(input_tomador)[0][1]

        return {
            'prob_fumador': round(prob_fumador * 100, 2),
            'prob_tomador': round(prob_tomador * 100, 2)
        }

    return {
        'modelo_fumador': modelo_fumador,
        'modelo_tomador': modelo_tomador,
        'encoders': encoders,
        'predecir': predecir
    }
