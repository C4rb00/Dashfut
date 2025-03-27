from flask import Flask, render_template, request
import pandas as pd
import plotly.graph_objs as go
import plotly.express as px
import plotly.io as pio

app = Flask(__name__)

# URLs para datasets
url_matches = 'https://raw.githubusercontent.com/daramireh/simonBolivarCienciaDatos/refs/heads/main/matches_1991_2023.csv'

# Cargar datos desde URL
df = pd.read_csv(url_matches)

# Asegurar tipos correctos de columnas
df['Year'] = df['Year'].astype(int)
df['home_team'] = df['home_team'].astype(str)
df['away_team'] = df['away_team'].astype(str)

# Lista de equipos
teams = sorted(set(df['home_team'].unique()) | set(df['away_team'].unique()))

# Función para filtrar partidos de un equipo
def get_team_matches(team):
    return df[(df['home_team'] == team) | (df['away_team'] == team)].copy()

# Gráfico 1: Estadísticas especiales
def graph_special_stats(team):
    df_team = get_team_matches(team)
    
    red_cards_count = df_team.apply(
        lambda row: row['home_red_card'] if row['home_team'] == team else row['away_red_card'],
        axis=1
    ).astype(str).apply(lambda x: 0 if x=='nan' or x=='' else len(x.split(','))).sum()
    
    subs_count = df_team.apply(
        lambda row: row['home_substitute_in_long'] if row['home_team'] == team else row['away_substitute_in_long'],
        axis=1
    ).astype(str).apply(lambda x: 0 if x=='nan' or x=='' else len(x.split(','))).sum()
    
    og_count = df_team.apply(
        lambda row: row['home_own_goal'] if row['home_team'] == team else row['away_own_goal'],
        axis=1
    ).astype(str).apply(lambda x: 0 if x=='nan' or x=='' else len(x.split(','))).sum()
    
    fig = go.Figure(data=[
        go.Bar(name='Tarjetas Rojas', x=['Tarjetas'], y=[red_cards_count], marker_color='crimson'),
        go.Bar(name='Sustituciones', x=['Sustituciones'], y=[subs_count], marker_color='orange'),
        go.Bar(name='Autogoles', x=['Autogoles'], y=[og_count], marker_color='gray')
    ])
    fig.update_layout(title=f'Estadísticas Especiales para {team}', yaxis_title='Cantidad', barmode='group')
    return pio.to_html(fig, full_html=False)

# Gráfico 2: Evolución de Asistencia
def graph_attendance_evolution(team):
    df_team = get_team_matches(team)
    att = df_team.groupby('Year')['Attendance'].agg(['mean','sum']).reset_index()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=att['Year'], y=att['mean'], mode='lines+markers',
                             name='Asistencia Promedio', line=dict(color='blue')))
    fig.add_trace(go.Scatter(x=att['Year'], y=att['sum'], mode='lines+markers',
                             name='Asistencia Total', line=dict(color='green')))
    fig.update_layout(title=f'Evolución de Asistencia para {team}', xaxis_title='Año', yaxis_title='Asistencia')
    return pio.to_html(fig, full_html=False)

# Gráfico 3: Distribución de Resultados
def graph_match_results(team):
    df_team = get_team_matches(team)
    def match_result(row):
        if row['home_team'] == team:
            return 'Win' if row['home_score'] > row['away_score'] else 'Loss' if row['home_score'] < row['away_score'] else 'Draw'
        else:
            return 'Win' if row['away_score'] > row['home_score'] else 'Loss' if row['away_score'] < row['home_score'] else 'Draw'
    df_team['Result'] = df_team.apply(match_result, axis=1)
    results = df_team['Result'].value_counts().to_dict()
    fig = px.pie(names=list(results.keys()), values=list(results.values()),
                 title=f'Distribución de Resultados para {team}')
    return pio.to_html(fig, full_html=False)

# Gráfico 4: Goles a Favor vs en Contra
def graph_goals_comparison(team):
    df_team = get_team_matches(team)
    goals_for = df_team.apply(lambda row: row['home_score'] if row['home_team']==team else row['away_score'], axis=1).sum()
    goals_against = df_team.apply(lambda row: row['away_score'] if row['home_team']==team else row['home_score'], axis=1).sum()
    fig = go.Figure(data=[
        go.Bar(name='Goles a Favor', x=[team], y=[goals_for], marker_color='teal'),
        go.Bar(name='Goles en Contra', x=[team], y=[goals_against], marker_color='salmon')
    ])
    fig.update_layout(title=f'Goles a Favor vs Goles en Contra para {team}', barmode='group', yaxis_title='Total de Goles')
    return pio.to_html(fig, full_html=False)

@app.route("/", methods=["GET", "POST"])
def index():
    selected_team = request.form.get("team") if request.method == "POST" else teams[0]

    plot_special = graph_special_stats(selected_team)
    plot_attendance = graph_attendance_evolution(selected_team)
    plot_results = graph_match_results(selected_team)
    plot_goals = graph_goals_comparison(selected_team)

    return render_template(
        "index.html",
        teams=teams,
        team=selected_team,
        plot_special=plot_special,
        plot_attendance=plot_attendance,
        plot_results=plot_results,
        plot_goals=plot_goals
    )
    
if __name__ == "__main__":
    app.run(debug=True)

server = app

