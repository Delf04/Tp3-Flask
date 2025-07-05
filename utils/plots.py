import matplotlib.pyplot as plt
import seaborn as sns
import os

DESCRIPCIONES_GRAFICOS = {
    "edad_inicio_fumar.png": "Distribución de edad de inicio al fumar.",
    "edad_inicio_beber.png": "Distribución de edad de inicio al beber alcohol.",
    "intentos_dejar_tomar.png": "Cantidad de intentos por dejar de tomar alcohol.",
    "distribucion_genero.png": "Proporción de género en la muestra.",
    "intentos_dejar_fumar.png": "Frecuencia de intentos de dejar de fumar.",
    "estado_salud_mental.png": "Estado de salud mental declarado por las personas.",
    "apoyo_social.png": "Niveles de apoyo social percibido.",
    "historial_terapia.png": "Historial de participación en terapia psicológica.",
    "edad_inicio_fumar_vs_cigarrillos.png": "Relación entre edad de inicio al fumar y cantidad fumada.",
    "edad_inicio_beber_vs_alcohol.png": "Relación entre edad de inicio al beber y cantidad de alcohol consumida.",
    "salud_mental_vs_empleo.png": "Cruce entre estado de salud mental y estado laboral.",
    "salud_mental_vs_estado_civil.png": "Cruce entre salud mental y estado civil.",
    "sueno_vs_dieta.png": "Relación entre horas de sueño y calidad de la dieta.",
    "sueno_vs_cigarrillos.png": "Relación entre sueño y cigarrillos por día.",
    "sueno_vs_alcohol.png": "Relación entre sueño y consumo de alcohol.",
    "intentos_dejar_fumar_vs_apoyo_social.png": "Intentos de dejar de fumar según el nivel de apoyo social.",
}
DESCRIPCIONES_ANALISIS = {
    'edad_inicio_fumar_vs_cigarrillos.png': 'Edad de inicio de fumar vs cigarrillos por día (promedio).',
    'edad_inicio_beber_vs_alcohol.png': 'Edad de inicio de beber vs consumo de alcohol semanal (promedio).',
    'salud_mental_vs_empleo.png': 'Mapa de calor entre estado de salud mental y estado laboral.',
    'salud_mental_vs_estado_civil.png': 'Mapa de calor entre salud mental y estado civil.',
    'sueno_vs_dieta.png': 'Boxplot de horas de sueño según calidad de dieta.',
    'sueno_vs_cigarrillos.png': 'Dispersión de horas de sueño y cigarrillos por día.',
    'sueno_vs_alcohol.png': 'Dispersión de horas de sueño y consumo de alcohol semanal.',
    'intentos_dejar_fumar_vs_apoyo_social.png': 'Intentos de dejar de fumar según nivel de apoyo social.'
}

def generar_graficos_generales(df, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    plot_files = []

    graficos = [
        ('Edad de inicio al fumar', 'age_started_smoking', 'orange', 'edad_inicio_fumar.png'),
        ('Edad de inicio al beber alcohol', 'age_started_drinking', 'green', 'edad_inicio_beber.png'),
        ('Intentos de dejar de tomar', 'attempts_to_quit_drinking', 'Purples', 'intentos_dejar_tomar.png'),
        ('Distribución de Género', 'gender', 'Set2', 'distribucion_genero.png'),
    ]

    for titulo, columna, color, filename in graficos:
        fig, ax = plt.subplots(figsize=(6, 4))
        if filename == 'edad_inicio_fumar.png' or filename == 'edad_inicio_beber.png':
            # Line chart para edad de inicio
            data = df[columna].dropna().value_counts().sort_index()
            ax.plot(data.index, data.values, marker='o', color=color)
            ax.set_xlabel('Edad')
            ax.set_ylabel('Cantidad de personas')
            ax.set_title(titulo)
        elif filename == 'distribucion_genero.png':
            # Pie chart para género
            counts = df[columna].value_counts(dropna=False)
            labels = counts.index.astype(str)
            ax.pie(counts, labels=labels, autopct='%1.1f%%', colors=sns.color_palette(color, len(counts)))
            ax.set_title(titulo)
            ax.axis('equal')
        elif df[columna].dtype == 'object' or df[columna].dtype.name == 'category' or len(df[columna].unique()) < 20:
            sns.countplot(x=columna, data=df, ax=ax, palette=color if isinstance(color, str) else None)
            ax.set_title(titulo)
        else:
            sns.histplot(df[columna].dropna(), bins=15, ax=ax, color=color)
            ax.set_title(titulo)
        path = os.path.join(output_dir, filename)
        fig.tight_layout()
        fig.savefig(path)
        plt.close(fig)
        plot_files.append(path)

    # Gráfico de barras para intentos de dejar de fumar
    fig, ax = plt.subplots(figsize=(6, 4))
    sns.countplot(x='attempts_to_quit_smoking', data=df, ax=ax, palette='Blues')
    ax.set_title('Intentos de dejar de fumar')
    ax.set_xlabel('Intentos')
    ax.set_ylabel('Cantidad de personas')
    fig.tight_layout()
    path = os.path.join(output_dir, 'intentos_dejar_fumar.png')
    fig.savefig(path)
    plt.close(fig)
    plot_files.append(path)

    # Gráfico de barras para mental health status
    fig, ax = plt.subplots(figsize=(6, 4))
    sns.countplot(x='mental_health_status', data=df, ax=ax, palette='Set3')
    ax.set_title('Estado de Salud Mental')
    ax.set_xlabel('Estado')
    ax.set_ylabel('Cantidad de personas')
    fig.tight_layout()
    path = os.path.join(output_dir, 'estado_salud_mental.png')
    fig.savefig(path)
    plt.close(fig)
    plot_files.append(path)

    # Gráfico de barras para social support
    fig, ax = plt.subplots(figsize=(6, 4))
    sns.countplot(x='social_support', data=df, ax=ax, palette='pastel')
    ax.set_title('Apoyo Social')
    ax.set_xlabel('Nivel de Apoyo')
    ax.set_ylabel('Cantidad de personas')
    fig.tight_layout()
    path = os.path.join(output_dir, 'apoyo_social.png')
    fig.savefig(path)
    plt.close(fig)
    plot_files.append(path)

    # Pie chart para therapy history
    fig, ax = plt.subplots(figsize=(6, 4))
    counts = df['therapy_history'].value_counts(dropna=False)
    labels = counts.index.astype(str)
    ax.pie(counts, labels=labels, autopct='%1.1f%%', colors=sns.color_palette('Set1', len(counts)))
    ax.set_title('Historial de Terapia')
    ax.axis('equal')
    fig.tight_layout()
    path = os.path.join(output_dir, 'historial_terapia.png')
    fig.savefig(path)
    plt.close(fig)
    plot_files.append(path)

    return plot_files

def generar_graficos_analisis(df, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    plot_files = []

    # Line charts para edad de inicio vs consumo
    line_charts = [
        ('Edad de inicio de fumar vs Cigarrillos por día', 'age_started_smoking', 'smokes_per_day', 'teal', 'edad_inicio_fumar_vs_cigarrillos.png'),
        ('Edad de inicio de beber vs Alcohol por semana', 'age_started_drinking', 'drinks_per_week', 'purple', 'edad_inicio_beber_vs_alcohol.png'),
    ]

    for titulo, x, y, color, filename in line_charts:
        fig, ax = plt.subplots(figsize=(6, 4))
        # Agrupar por edad de inicio y calcular promedio de consumo
        grouped = df[[x, y]].dropna().groupby(x)[y].mean()
        ax.plot(grouped.index, grouped.values, marker='o', color=color)
        ax.set_xlabel(x.replace('_', ' ').capitalize())
        ax.set_ylabel(f'Promedio de {y.replace("_", " ")}')
        ax.set_title(titulo)
        fig.tight_layout()
        path = os.path.join(output_dir, filename)
        fig.savefig(path)
        plt.close(fig)
        plot_files.append(path)

    # Comparar mental health status con employment status (heatmap)
    fig, ax = plt.subplots(figsize=(6, 4))
    pivot = df.pivot_table(index='mental_health_status', columns='employment_status', aggfunc='size', fill_value=0)
    sns.heatmap(pivot, annot=True, fmt='d', cmap='YlGnBu', ax=ax)
    ax.set_title('Salud Mental vs Estado Laboral')
    fig.tight_layout()
    path = os.path.join(output_dir, 'salud_mental_vs_empleo.png')
    fig.savefig(path)
    plt.close(fig)
    plot_files.append(path)

    # Comparar mental health status con marital status (heatmap)
    fig, ax = plt.subplots(figsize=(6, 4))
    pivot = df.pivot_table(index='mental_health_status', columns='marital_status', aggfunc='size', fill_value=0)
    sns.heatmap(pivot, annot=True, fmt='d', cmap='YlOrRd', ax=ax)
    ax.set_title('Salud Mental vs Estado Civil')
    fig.tight_layout()
    path = os.path.join(output_dir, 'salud_mental_vs_estado_civil.png')
    fig.savefig(path)
    plt.close(fig)
    plot_files.append(path)

    # Horas de sueño vs diet quality (boxplot)
    fig, ax = plt.subplots(figsize=(6, 4))
    sns.boxplot(x='diet_quality', y='sleep_hours', data=df, ax=ax, palette='Set2')
    ax.set_title('Horas de Sueño según Calidad de Dieta')
    ax.set_xlabel('Calidad de Dieta')
    ax.set_ylabel('Horas de Sueño')
    fig.tight_layout()
    path = os.path.join(output_dir, 'sueno_vs_dieta.png')
    fig.savefig(path)
    plt.close(fig)
    plot_files.append(path)

    # Horas de sueño vs cigarrillos por semana (scatter)
    fig, ax = plt.subplots(figsize=(6, 4))
    sns.scatterplot(x='sleep_hours', y='smokes_per_day', data=df, ax=ax, color='blue', alpha=0.6)
    ax.set_title('Horas de Sueño vs Cigarrillos por Día')
    ax.set_xlabel('Horas de Sueño')
    ax.set_ylabel('Cigarrillos por Día')
    fig.tight_layout()
    path = os.path.join(output_dir, 'sueno_vs_cigarrillos.png')
    fig.savefig(path)
    plt.close(fig)
    plot_files.append(path)

    # Horas de sueño vs alcohol por semana (scatter)
    fig, ax = plt.subplots(figsize=(6, 4))
    sns.scatterplot(x='sleep_hours', y='drinks_per_week', data=df, ax=ax, color='green', alpha=0.6)
    ax.set_title('Horas de Sueño vs Alcohol por Semana')
    ax.set_xlabel('Horas de Sueño')
    ax.set_ylabel('Alcohol por Semana')
    fig.tight_layout()
    path = os.path.join(output_dir, 'sueno_vs_alcohol.png')
    fig.savefig(path)
    plt.close(fig)
    plot_files.append(path)

    # Boxplot adicional
    fig, ax = plt.subplots(figsize=(6, 4))
    sns.boxplot(
        x='social_support',
        y='attempts_to_quit_smoking',
        data=df,
        ax=ax,
        palette='pastel'
    )
    ax.set_title('Intentos de dejar de fumar según Apoyo Social')
    ax.tick_params(axis='x', rotation=30)
    fig.tight_layout()
    path = os.path.join(output_dir, 'intentos_dejar_fumar_vs_apoyo_social.png')
    fig.savefig(path)
    plt.close(fig)
    plot_files.append(path)

    return plot_files