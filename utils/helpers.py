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
                therapy_history=row['therapy_history']
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

    df['es_fumador_frecuente'] = df['smokes_per_day'] > 10
    df['es_tomador_frecuente'] = df['drinks_per_week'] > 7

    features = ['age', 'gender', 'smokes_per_day', 'age_started_smoking',
                'attempts_to_quit_smoking', 'has_health_issues', 'mental_health_status']

    features_tomador = ['age', 'gender', 'smokes_per_day', 'age_started_drinking',
                        'attempts_to_quit_drinking', 'has_health_issues', 'mental_health_status']

    X_fumador = df[features].copy()
    y_fumador = df['es_fumador_frecuente'].astype(int)
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

    modelo_fumador = LogisticRegression(max_iter=1000).fit(X_fumador, y_fumador)
    modelo_tomador = LogisticRegression(max_iter=1000).fit(X_tomador, y_tomador)

    def predecir(input_dict):
        age = int(input_dict['age'])
        gender_encoded = le_gender.transform([input_dict['gender']])[0]
        mental_encoded = le_mental.transform([input_dict['mental_health_status']])[0]
        has_health_issues = input_dict['has_health_issues'] == 'true'

        input_fumador = np.array([[
            age, gender_encoded, int(input_dict['smokes_per_day']),
            int(input_dict['age_started_smoking']), int(input_dict['attempts_to_quit_smoking']),
            int(has_health_issues), mental_encoded
        ]])

        input_tomador = np.array([[
            age, gender_encoded, int(input_dict['smokes_per_day']),
            int(input_dict['age_started_drinking']), int(input_dict['attempts_to_quit_drinking']),
            int(has_health_issues), mental_encoded
        ]])

        prob_fumador = modelo_fumador.predict_proba(input_fumador)[0][1]
        prob_tomador = modelo_tomador.predict_proba(input_tomador)[0][1]

        return {
            'prob_fumador': round(prob_fumador * 100, 2),
            'prob_tomador': round(prob_tomador * 100, 2)
        }

    return {
        'modelo_fumador': modelo_fumador,
        'modelo_tomador': modelo_tomador,
        'encoder_gender': le_gender,
        'encoder_mental': le_mental,
        'predecir': predecir
    }