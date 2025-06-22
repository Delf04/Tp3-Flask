import matplotlib.pyplot as plt
import seaborn as sns
import os

def generar_graficos_generales(df, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    plot_files = []

    graficos = [
        ('Edad de inicio al fumar', 'age_started_smoking', 'orange', 'edad_inicio_fumar.png'),
        ('Edad de inicio al beber alcohol', 'age_started_drinking', 'green', 'edad_inicio_beber.png'),
        ('Intentos de dejar de tomar', 'attempts_to_quit_drinking', 'Purples', 'intentos_dejar_tomar.png'),
        ('Distribución de Género', 'gender', 'Set2', 'distribucion_genero.png'),
        ('Distribución de Problemas de Salud', 'has_health_issues', 'Set1', 'distribucion_salud.png'),
    ]

    for titulo, columna, color, filename in graficos:
        fig, ax = plt.subplots(figsize=(6, 4))
        if df[columna].dtype == 'object' or df[columna].dtype.name == 'category' or len(df[columna].unique()) < 20:
            sns.countplot(x=columna, data=df, ax=ax, palette=color if isinstance(color, str) else None)
        else:
            sns.histplot(df[columna].dropna(), bins=15, ax=ax, color=color)
        ax.set_title(titulo)
        path = os.path.join(output_dir, filename)
        fig.tight_layout()
        fig.savefig(path)
        plt.close(fig)
        plot_files.append(path)

    # Gráficos relacionales
    relacionales = [
        ('Edad vs Consumo de Alcohol por Semana', 'age', 'drinks_per_week', 'edad_vs_alcohol.png'),
        ('Cigarrillos por día vs Alcohol por semana', 'smokes_per_day', 'drinks_per_week', 'cigarrillos_vs_alcohol.png'),
    ]
    for titulo, x, y, filename in relacionales:
        fig, ax = plt.subplots(figsize=(6, 4))
        sns.scatterplot(x=x, y=y, data=df, ax=ax, alpha=0.6)
        ax.set_title(titulo)
        path = os.path.join(output_dir, filename)
        fig.tight_layout()
        fig.savefig(path)
        plt.close(fig)
        plot_files.append(path)

    return plot_files

def generar_graficos_analisis(df, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    plot_files = []

    analisis = [
        ('Edad de inicio de fumar vs Cigarrillos por día', 'age_started_smoking', 'smokes_per_day', 'teal', 'edad_inicio_fumar_vs_cigarrillos.png'),
        ('Edad de inicio de beber vs Alcohol por semana', 'age_started_drinking', 'drinks_per_week', 'purple', 'edad_inicio_beber_vs_alcohol.png'),
    ]

    for titulo, x, y, color, filename in analisis:
        fig, ax = plt.subplots(figsize=(6, 4))
        sns.scatterplot(x=x, y=y, data=df, ax=ax, alpha=0.6, color=color)
        ax.set_title(titulo)
        fig.tight_layout()
        path = os.path.join(output_dir, filename)
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