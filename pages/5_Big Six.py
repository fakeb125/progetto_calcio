import altair as alt
import polars as pl
import pandas as pd
import streamlit as st
import numpy as np
import matplotlib.colors as mcolors


# ===============================
# 1. FUNZIONI FACILITATRICI
# ===============================


# Funzione di caricamento dati
def carica_dati(path: str):
    return pl.read_csv(path, null_values=["", "NA ", " NA", "NA"])


# ====================================================
# 2. OPERAZIONI DI PREPARAZIONE DEI DATASET
# ====================================================


# Caricamento dei dataset, completati e ordinati
df_h2h   = carica_dati("h2h_premier.csv") 
df_matches   = carica_dati("largest_win.csv") 


# Lista ordinata di tutte le squadre
unique_teams = sorted(df_matches["home"].unique().to_list())


# -------------------------
# 2.1) Matrice Vittorie Casalinghe

# Costruisco la Matrice
rows_home = []
for h in unique_teams:
    row = {"home": h}
    for a in unique_teams:
        if a == h:
            row[a] = ""
        else:
            sub = df_matches.filter(
                (pl.col("home") == h) & (pl.col("away") == a)
            )
            if sub.is_empty():
                row[a] = ""
            else:
                row[a] = sub[0, "home_win"]
    rows_home.append(row)

wide_home_win_df = pl.DataFrame(rows_home)
home_win_pd = wide_home_win_df.to_pandas().set_index("home")

# Differenza Reti per Vittoria in Casa
rows_home_diff = []
for h in unique_teams:
    diff_row = {"home": h}
    for a in unique_teams:
        if a == h:
            diff_row[a] = np.nan
        else:
            sub = df_matches.filter(
                (pl.col("home") == h) & (pl.col("away") == a)
            )
            diff_row[a] = sub[0, "home_diff"] if not sub.is_empty() else np.nan
    rows_home_diff.append(diff_row)

wide_home_diff_df = pl.DataFrame(rows_home_diff)
home_diff_pd = wide_home_diff_df.to_pandas().set_index("home")


# -------------------------
# 2.2) Matrice Sconfitte Casalinghe

# Costruisco la Matrice
rows_away = []
for h in unique_teams:  # ora “h” è la squadra di casa (indice di riga)
    row = {"home": h}
    for a in unique_teams:  # “a” è la squadra in trasferta (colonna)
        if a == h:
            row[a] = ""
        else:
            sub = df_matches.filter(
                (pl.col("home") == h) & (pl.col("away") == a)
            )
            if sub.is_empty():
                row[a] = ""
            else:
                row[a] = sub[0, "away_win"]
    rows_away.append(row)

wide_away_win_df = pl.DataFrame(rows_away)
away_win_pd = wide_away_win_df.to_pandas().set_index("home")

# Differenzaa Reti per Sconfitte in Casa
rows_away_diff = []
for h in unique_teams:  # “h” è la squadra di casa (indice di riga)
    diff_row = {"home": h}
    for a in unique_teams:  # “a” è la squadra in trasferta (colonna)
        if a == h:
            diff_row[a] = np.nan
        else:
            sub = df_matches.filter(
                (pl.col("home") == h) & (pl.col("away") == a)
            )
            diff_row[a] = sub[0, "away_diff"] if not sub.is_empty() else np.nan
    rows_away_diff.append(diff_row)

wide_away_diff_df = pl.DataFrame(rows_away_diff)
away_diff_pd = wide_away_diff_df.to_pandas().set_index("home")


# -------------------------
# 2.3) Valori Minimi e Massimi di goal difference

all_min = min(
    home_diff_pd.min().min(skipna=True),
    away_diff_pd.min().min(skipna=True)
)
all_max = max(
    home_diff_pd.max().max(skipna=True),
    away_diff_pd.max().max(skipna=True)
)

vmin = int(all_min)
vmax = int(all_max) 


# -------------------------
# 2.4) Dataframe per Heatmap


# Costruisco la lista completa di squadre in df_h2h
unique_teams_h2h = sorted(
    set(df_h2h["team1"].unique().to_list() + df_h2h["team2"].unique().to_list())
)

# Creo una lista di dizionari {'team1': t1, 'team2': t2, 'net': net_round, 'V': V, 'S': S}
data_list = []
for t1 in unique_teams_h2h:
    for t2 in unique_teams_h2h:
        if t1 == t2:
            net = np.nan
            V = 0
            S = 0
        else:
            sub1 = df_h2h.filter(
                (pl.col("team1") == t1) & (pl.col("team2") == t2)
            )
            if not sub1.is_empty():
                V = int(sub1[0, "win1"])
                S = int(sub1[0, "win2"])
            else:
                sub2 = df_h2h.filter(
                    (pl.col("team1") == t2) & (pl.col("team2") == t1)
                )
                if not sub2.is_empty():
                    V = int(sub2[0, "win2"])
                    S = int(sub2[0, "win1"])
                else:
                    V = 0
                    S = 0
            net = round(V - S)
        data_list.append({"team1": t1, "team2": t2, "net": net, "V": V, "S": S})

# Converto in pandas DataFrame
heatmap_df = pd.DataFrame(data_list)

# Trovo il valore massimo assoluto di “net” per definire una scala simmetrica
max_abs = int(max(
    heatmap_df["net"].max(skipna=True),
    abs(heatmap_df["net"].min(skipna=True))
))



# =======================================
# 3. VISUALIZZAZIONE CON STREAMLIT E Altair
# =======================================


# 3.1) Introduzione

st.subheader("Scontri tra le Big (Rich) Six della Premier League")
st.markdown("Nel corso dell’era Premier League, le cosiddette “Big Six” — Arsenal, Chelsea, Liverpool, Manchester City, Manchester United e Tottenham" \
" — hanno dato vita a una fitta rete di **scontri diretti** che hanno spesso deciso le sorti del campionato.    \n" \
"In questa sezione vengono analizzati i confronti tra queste sei squadre, sia in termini di vittorie più nette (in casa e in trasferta)," \
" sia attraverso una heatmap che sintetizza il bilancio netto di vittorie e sconfitte.  \n" \
"Le matrici permettono di identificare quali club si siano imposti con maggiore frequenza sugli altri, offrendo uno sguardo comparativo" \
" sui risultati più dominanti e sulle debolezze più ricorrenti tra le protagoniste della lega.")

st.divider()


# -------------------------
# Preparo le Matrici

custom_cmap = mcolors.LinearSegmentedColormap.from_list(
    "rossobiancoverde",
    ["#d7191c", "#f7f7f7", "#1a9641"]
)

# Definisco una Funzione per associare i colori ai valori normalizzati tra min e max
def color_cell(val, vmin=vmin, vmax=vmax, cmap=custom_cmap):
    if pd.isna(val):
        return "background-color: transparent; text-align: center;"
    norm = (val - vmin) / (vmax - vmin)
    norm = min(max(norm, 0.0), 1.0)
    rgba = cmap(norm)
    hexcol = mcolors.to_hex(rgba)
    return f"background-color: {hexcol}; color: black; text-align: center;"

# Assegno colori alla Matrice Vittorie Casalinghe
styled_home = home_win_pd.style.apply(
    lambda row: [
        color_cell(home_diff_pd.loc[row.name, col])
        for col in home_win_pd.columns
    ],
    axis=1
).set_properties(**{"text-align": "center"})

# Assegno colori alla Matrice Sconfitte Casalinghe
styled_away = away_win_pd.style.apply(
    lambda row: [
        color_cell(away_diff_pd.loc[row.name, col])
        for col in away_win_pd.columns
    ],
    axis=1
).set_properties(**{"text-align": "center"})


# -------------------------
# 3.2) Matrice Vittorie Casalinghe

st.subheader("Matrice delle Migliori Vittorie in Casa")
st.caption("Vittoria della Squadra nella prima colonna (squadra in casa), colorata per differenza reti")
st.dataframe(styled_home, use_container_width=True)
st.markdown("Il Manchester United detiene la vittoria casalinga più imponente tra le Big Six, segnando in un match addirittura **8 goal** ai danni dell’Arsenal.   \n"
"Liverpool si distingue per la costanza della sua forza offensiva in casa: ha rifilato **almeno 5 gol a ciascuna** delle altre Big Six, con i due 7-0 inflitti"
" a Manchester United e Tottenham che rappresentano i massimi scarti della tabella.  \n"
"Al contrario, l’Arsenal risulta l’unica squadra a non aver mai ottenuto una vittoria interna eccessivamente dominante, fermandosi a un **massimo di 3 reti di scarto**.    \n"
"Manchester City e Chelsea appaiono solidi tra le mura amiche, con diversi successi larghi, in particolare il 6-0 inflitto dal City proprio ai Blues.")

st.divider()


# -------------------------
# 3.3) Matrice Sconfitte Casalinghe

st.subheader("Matrice delle Peggiori Sconfitte in Casa")
st.caption("Sconfitta della Squadra nella prima colonna (squadra in casa), colorata per differenza reti (stessa scala)")
st.dataframe(styled_away, use_container_width=True)
st.markdown("Il Tottenham ha collezionato pessime figure casalinghe contro tutte le altre squadre della tabella, **subendo almeno 5 gol da ogni rivale**.   \n" \
"Lo United ha incassato **6 gol in casa** per ben due volte, una rarità per un club del suo livello.    \n" \
"L’Arsenal, così come non ha mai vinto dominando in casa, non ha mai perso in casa con scarti umilianti: tutte le sue sconfitte interne sono rimaste contenute. \n" \
"Chelsea e City mostrano una vulnerabilità più discontinua: pur con qualche tonfo interno evidente," \
" non raggiungono la frequenza o la gravità delle sconfitte subite da Tottenham e United.")

st.divider()


# -------------------------
# 3.4) HEATMAP HEAD-TO-HEAD: BILANCIO NETTO (V–S)

# Costruisco la heatmap 
heatmap = (
    alt.Chart(heatmap_df)
    .mark_rect()
    .encode(
        x=alt.X(
            "team2:O",
            title="Team 2",
            sort=unique_teams_h2h,
            axis=alt.Axis(labelAngle=0, labelAlign="center", labelFontSize=10)
        ),
        y=alt.Y(
            "team1:O",
            title=None,
            sort=unique_teams_h2h,
            axis=alt.Axis(labelAngle=0, labelAlign="right", labelFontSize=10)
        ),
        color=alt.Color(
            "net:Q",
            title="Net (V–S)",
            scale=alt.Scale(
                scheme="redyellowgreen",
                domain=[-max_abs, max_abs],
                clamp=True
            ),
            legend=alt.Legend(title="V–S", orient="right", tickCount=7, titleFontSize=12, labelFontSize=10)
        ),
        tooltip=[
            alt.Tooltip("team1:O", title="Team 1"),
            alt.Tooltip("team2:O", title="Team 2"),
            alt.Tooltip("net:Q", format="d", title="V–S"),
            alt.Tooltip("V:O", title="win1"),
            alt.Tooltip("S:O", title="win2")
        ]
    )
    .properties(
        width=800,
        height=600,
        background="#f0f0f0",
        padding={"left": 10, "right": 0, "top": 20, "bottom": 20}
    )
    .configure_axis(
        labelAngle=-45,
        labelAlign="left"
    )
)

st.subheader("Bilanci Storici negli Scontri Diretti tra le Big Six")
st.caption(
    "Heatmap con bilanci netti (V–S) tra le Big Six: asse Y = Team 1 , asse X = Team 2  \n"
    "Valore calcolato come vittorie di Team 1 (win1) - vittorie di Team 2 (win2)."
)
st.altair_chart(heatmap, use_container_width=True)
st.markdown("Il Tottenham Hotspur registra il bilancio **più sfavorevole** contro tutte le altre big, con saldi particolarmente" \
" negativi nei confronti di Chelsea e Manchester United.    \nIl Manchester City è l’unica squadra con un saldo negativo nei confronti" \
" di **tutte** le rimanenti cinque, nonostante i successi nazionali recenti.    \nI compaesani dello United al contrario hanno **saldo** " \
"**positivo** contro tutte, se non fosse per quella vittoria in meno a favor del Chelsea    \n" \
"Le altre squadre hanno un rapporto piuttosto equilibrato tra di loro.")

st.divider()


# -------------------------
# 3.5 Mostra Dataset

if "mostra_dataset" not in st.session_state:
    st.session_state.mostra_dataset = False

if st.button("Mostra dataset"):
    st.session_state.mostra_dataset = not st.session_state.mostra_dataset

if st.session_state.mostra_dataset:

    # 1) df_h2h
    st.markdown("**df_h2h** (copied): statistiche testa-a-testa tra le squadre")
    st.dataframe(df_h2h, use_container_width=True)

    st.divider()

    # 2) df_matches
    st.markdown("**df_matches** (copied): dataset degli scontri più pesanti tra i team")
    st.dataframe(df_matches, use_container_width=True)

    st.markdown(
        "I dati sono stati ricavati dal sito ufficiale [Premier League](https://www.premierleague.com/stats/head-to-head)" \
        " e cercando su Wikipedia in pagine dedicate agli scontri storici tra le squadre"
    )

    # Nascondi Dataset
    st.markdown("<br><br><br>*Per nascondere i dataset, premere due volte il pulsante.*", unsafe_allow_html=True)
    if st.button("Nascondi dataset"):
        st.session_state.mostra_dataset = False