import altair as alt
import polars as pl
import pandas as pd
import streamlit as st


# ===============================
# 1. FUNZIONE FACILITATRICI
# ===============================


# Funzione di caricamento dati
def carica_dati(path: str):
    return pl.read_csv(path, null_values=["", "NA ", " NA", "NA"])


# Evidenziare una riga di dataset
def evidenzia_squadra(squadra: str, colore_hex: str): # Usa i codici HEX
    def highlight(row):
        if row["Squadra"] == squadra:
            return [f'background-color: {colore_hex}55'] * len(row)  # '55' è ~30% opacità
        else:
            return [''] * len(row)
    return highlight



# ====================================================
# 2. OPERAZIONI DI PREPARAZIONE DEI DATASET
# ====================================================


# Caricamento dei dataset
df_winners   = carica_dati("principale.csv")
df_age   = carica_dati("average_age.csv")
df_topscorer = carica_dati("top_scorer.csv")

# --------------------
# 2.1 età lega

# Calcolo per età estreme (3ª e 5ª squadra più giovane/vecchia) per ciascun anno
df_353 = (
    df_age
    .group_by("Anno")
    .agg([
        pl.col("Average_age").sort().slice(2, 1).alias("lower3_list"),
        pl.col("Average_age").sort().slice(4, 1).alias("lower5_list"),
        pl.col("Average_age").sort(descending=True).slice(2, 1).alias("upper3_list"),
        pl.col("Average_age").sort(descending=True).slice(4, 1).alias("upper5_list"),
        pl.col("Average_age").mean().round(2).alias("league_mean")
    ])
    .with_columns([
        pl.col("lower3_list").list.get(0).alias("lower3"),
        pl.col("lower5_list").list.get(0).alias("lower5"),
        pl.col("upper3_list").list.get(0).alias("upper3"),
        pl.col("upper5_list").list.get(0).alias("upper5"),
        (pl.col("Anno") + 1).alias("Anno_end")
    ])
    .drop(["lower3_list", "lower5_list", "upper3_list", "upper5_list"])
)

# Aggiungo il vincitore e la sua età media da df_winners (che ha già l'Average_age per ciascun vincitore)
df_353 = df_353.join(
    df_winners.select(["Anno", "Vincitore", "Average_age"]),
    on="Anno",
    how="left"
).sort("Anno")

# Converto in pandas per Altair
df_353_pd = df_353.to_pandas()

# --------------------
# 2.2 chelsea

# Estraggo Chelsea average age da df_age
chelsea_avg = (
    df_age
    .filter(pl.col("Squadra") == "Chelsea FC")
    .select([
        pl.col("Anno"),
        pl.col("Average_age").round(2).alias("Chelsea_avg")
    ])
)

df_chelsea = (
    df_winners.select(["Stagione","League_average_age", "Anno"]).rename({"League_average_age":"League_avg"})
    .join(chelsea_avg, on="Anno", how="inner")
    # .join(chelsea_points, on="Anno", how="inner")
    .sort("Anno")
)
df_chelsea_pd = df_chelsea.to_pandas()



# ====================================================
# 3. VISUALIZZAZIONE CON STREAMLIT E Altair
# ====================================================


# 3.1) Grafico: distribuzione 3ª/5ª Squadra + linee Lega e Vincitore

# 1) Definisco una selezione per il mouseover su 'Anno'
selector_353 = alt.selection_single(
    fields=["Anno"],
    nearest=True,
    on="mouseover",
    empty="none",
    clear="mouseout"
)

# 2) Banda più ampia: dalla 3ª più giovane (lower3) alla 3ª più vecchia (upper3)
area_banda_ampia = alt.Chart(df_353_pd).mark_area(
    color="#90ee90",  # verde chiaro
    opacity=0.3
).encode(
    x=alt.X("Anno:Q", axis=alt.Axis(title=None, format='d')),
    x2=alt.X2("Anno_end"),
    y=alt.Y("lower3:Q", title=None, scale=alt.Scale(domain=[24, 29])),
    y2="upper3:Q"
)

# 3) Banda più stretta: dalla 5ª più giovane (lower5) alla 5ª più vecchia (upper5)
area_banda_stretta = alt.Chart(df_353_pd).mark_area(
    color="#32cd32",  # verde lime
    opacity=0.4
).encode(
    x=alt.X("Anno:Q"),
    x2=alt.X2("Anno_end"),
    y="lower5:Q",
    y2="upper5:Q"
)

# 4) Linea media Lega
line_league0 = alt.Chart(df_353_pd).mark_line(
    color="#228B22"
).encode(
    x="Anno:Q",
    y="league_mean:Q"
)

point_league = alt.Chart(df_353_pd).mark_circle(
    color="#228B22", size=50  
).encode(
    x="Anno:Q",
    y="league_mean:Q"
)

line_league = line_league0 + point_league

# 5) Linea squadra vincitrice
line_winner0 = alt.Chart(df_353_pd).mark_line(
    color="crimson"
).encode(
    x="Anno:Q",
    y="Average_age:Q"
)

point_winner = alt.Chart(df_353_pd).mark_circle(
    color="crimson", size=50  
).encode(
    x="Anno:Q",
    y="Average_age:Q"
)

line_winner = line_winner0 + point_winner

# 6) Rettangolo invisibile per il tooltip
rect_hover_353 = alt.Chart(df_353_pd).mark_rect(opacity=0).encode(
    x="Anno:Q",
    x2=alt.X2("Anno_end"),
    y=alt.value(22),
    y2=alt.value(32),
    tooltip=[
        alt.Tooltip("Vincitore:N", title="Vincitore"),
        alt.Tooltip("Anno:Q", title="Anno", format=".0f"),
        alt.Tooltip("league_mean:Q", title="Media Lega", format=".2f"),
        alt.Tooltip("Average_age:Q", title="Età Vinc.", format=".2f")
    ]
).add_selection(selector_353)

# 7) Barra verticale
vertical_line_353 = alt.Chart(df_353_pd).mark_rule(
    color="black",
    strokeDash=[4, 4],
    strokeWidth=1
).encode(
    x="Anno:Q"
).transform_filter(selector_353)

# 8) Composizione finale con alt.layer
final_chart_353 = alt.layer(
    area_banda_ampia,     
    area_banda_stretta,
    line_league,       
    line_winner,       
    rect_hover_353,
    vertical_line_353 
).properties(
    width=800,
    height=400,
    background="#f0f0f0",
    padding={"left": 20, "right": 20, "top": 20, "bottom": 20}
).configure_view(
    strokeWidth=0
).configure_axis(
    labelFontSize=12,
    titleFontSize=14
).resolve_scale(
    y='shared'
)


st.subheader("Vincitore e Profilo Anagrafico della Lega a Confronto")
st.caption(
    "Le bande indicano le età comprese tra la 3ª e la 5ª squadra più giovane e la 3ª e la 5ª meno giovane della stagione:  \n"
    "banda chiara tra le terze, banda scura tra le quinte. Linea Rossa = vincitore, Linea Verde = media della lega."
)
st.altair_chart(final_chart_353, use_container_width=True)
st.markdown("Il confronto diretto tra le età medie delle squadre vincitrici e quelle della lega non sembra rivelare una regolarità chiara nel tempo."\
" Alcune squadre hanno conquistato il titolo con rose mediamente molto giovani, altre con organici più esperti.     \n" \
" Un dato particolarmente interessante riguarda il Chelsea FC, che detiene il primato sia per aver vinto con la squadra più giovane"
" (nel 2004/05, con un’età media di **25 anni**) sia per aver trionfato con la più anziana (nel 2009/10, **28.2 anni**). " \
"Ciò suggerisce che non esiste un’età “ottimale” per vincere, e che la composizione anagrafica delle squadre può essere molto varia anche tra i campioni.   \n" \
" Il fattore età, in altre parole, non sembra essere una discriminante determinante nei successi in Premier League.")

st.divider()


# ------------------
# 3.2) DIFFERENZA

# Preparo i dati
df_differenza = df_winners.with_columns(
    (pl.col("Average_age") - pl.col("League_average_age")).alias("Differenza")
)
df_differenza_pd = df_differenza.to_pandas()

# Selettore
selector_diff = alt.selection_single(
    fields=["Anno"],
    nearest=True,
    on="mouseover",
    empty="none",
    clear="mouseout"
)

# Base chart (x come Ordinal)
base = alt.Chart(df_differenza_pd).encode(
    x=alt.X("Anno:O", title=None, axis=alt.Axis(labelAngle=0))
)

# Linea principale
diff_line = base.mark_line(point=alt.OverlayMarkDef(filled=True, fill="blue"), color="green").encode(
    y=alt.Y("Differenza:Q", title=None,
        scale=alt.Scale(domain=[
            df_differenza_pd["Differenza"].min(),
            df_differenza_pd["Differenza"].max() + 0.5 
        ])
    )
)

# Linea rossa sullo 0
zero_line = alt.Chart(pd.DataFrame({'y': [0]})).mark_rule(
    color='red', strokeWidth=2
).encode(y='y:Q')

# Rettangolo invisibile per il selettore
rect_hover = alt.Chart(df_differenza_pd).mark_rect(opacity=0).encode(
    x=alt.X("Anno:O"),
    tooltip=[
        alt.Tooltip("Anno:O", title=None),
        alt.Tooltip("Vincitore:N", title="Vincitore"),
        alt.Tooltip("Differenza:Q", title="Differenza", format=".2f")
    ]
).add_selection(selector_diff)

# Barra verticale che segue il selettore
vertical_rule = alt.Chart(df_differenza_pd).mark_rule(
    color="black", strokeDash=[4, 4], strokeWidth=1
).encode(
    x=alt.X("Anno:O"),
    opacity=alt.condition(selector_diff, alt.value(1), alt.value(0))
)

# Composizione finale
final_diff = (
    diff_line +
    zero_line +
    rect_hover +
    vertical_rule
).properties(
    width=800,
    height=400,
    background="#f0f0f0",
    padding={"left": 20, "right": 20, "top": 20, "bottom": 20}
).configure_axis(
    labelFontSize=12,
    titleFontSize=14,
    grid=True
).configure_view(
    strokeWidth=0
)


st.subheader("Differenza Età Media: Vincitore vs Lega")
st.caption("La linea evidenzia quanto la squadra vincente si discosti in termini anagrafici dalla media complessiva del campionato.")
st.altair_chart(final_diff, use_container_width=True)
st.markdown("La differenza tra l’età media del vincitore " \
"e quella della lega oscilla leggermente attorno allo zero, **senza evidenziare una tendenza costante**." \
" Le stagioni con scostamenti più marcati sono isolate e sembrano più legate a contesti specifici che a un trend strutturale.")

st.divider()


# -------------
# 3.3) Chelsea

# Definisco una selezione per il mouseover su 'Anno'
selector_che = alt.selection_single(
    fields=["Anno"],
    nearest=True,
    on="mouseover",
    empty="none",
    clear="mouseout"
)

# Base chart con asse X ordinato per stagione ---
base = alt.Chart(df_chelsea_pd).encode(
    x=alt.X("Anno:O",
            axis=alt.Axis(labelAngle=0, labelFontSize=12),
            title=None),
    tooltip=[
        alt.Tooltip("Anno:O", title="Stagione"),
        alt.Tooltip("League_avg:Q", title="Media Lega", format=".2f"),
        alt.Tooltip("Chelsea_avg:Q", title="Media Chelsea", format=".2f")
    ]
)

# Linea Media Lega (verde) ---
league_line = base.mark_line(color="#228B22", strokeWidth=2, opacity=0.4).encode(
    y=alt.Y("League_avg:Q", title=None, scale=alt.Scale(domain=[23,29]))
)

# Linea e punti Media Chelsea (blu) ---
chelsea_line = base.mark_line(color="#001F5C", strokeWidth=2.5).encode(
    y="Chelsea_avg:Q"
)

champ_years = [2004, 2005, 2009, 2014, 2016]
win_points = (
    alt.Chart(
        pd.DataFrame({"Anno": champ_years, 
                      "Chelsea_avg": df_chelsea_pd.set_index("Anno").loc[champ_years, "Chelsea_avg"].values})
    )
    .mark_point(shape="circle", size=100, filled=False, color="red", strokeWidth=2)
    .encode(
        x=alt.X("Anno:O"),
        y=alt.Y("Chelsea_avg:Q")
    )
)

# Rolling mean 5-stagioni del Chelsea (rossa tratteggiata) ---
rolling_line = (
    base.transform_window(
        rolling_age="mean(Chelsea_avg)",
        frame=[-2, 2]     
    )
    .mark_line(color="red", strokeWidth=2, strokeDash=[4,2])
    .encode(
        y="rolling_age:Q"
    )
)

# Rettangolo invisibile per il tooltip (su tutta l'altezza del grafico)
rect_hover_che = (
    alt.Chart(df_chelsea_pd)
      .mark_rect(opacity=0)
      .encode(
          x=alt.X("Anno:O"),
          tooltip=[
            alt.Tooltip("Anno:O", title="Stagione"),
            alt.Tooltip("Chelsea_avg:Q", title="Età Chelsea", format=".2f"),
            alt.Tooltip("League_avg:Q", title="Età Lega",    format=".2f"),
          ]
      )
      .add_selection(selector_che)
)

# Barra verticale che appare al passaggio sullo stesso 'Anno'
vertical_line_che = (
    alt.Chart(df_chelsea_pd)
      .mark_rule(color="black", strokeDash=[4,4], strokeWidth=1)
      .encode(
          x=alt.X("Anno:O"),
          opacity=alt.condition(selector_che, alt.value(1), alt.value(0))
      )
)


# --- Composizione finale ---
combined = (
    league_line
    + chelsea_line
    + win_points
    + rolling_line
    + rect_hover_che
    + vertical_line_che
).properties(
    width=800,
    height=400,
    padding={"left":20,"right":20,"top":20,"bottom":20},
    background="#f0f0f0"
).configure_title(
    fontSize=16,
    fontWeight="bold",
    anchor="middle"
).configure_axis(
    labelFontSize=12
)


st.subheader("Evoluzione Età Media: Chelsea FC")
st.caption(
    "La linea rossa liscia l'andamento dell'età media, i tondi rossi rappresentano gli anni in cui il Chelsea ha vinto il titolo.  \n" \
"Per la Rolling Mean sono state prese in considerazione 5 stagioni"
)
st.altair_chart(combined, use_container_width=True)

st.markdown(
    "A partire dal 2003 si osserva un netto calo dell’età media del Chelsea, che può essere interpretato come l’avvio di un **nuovo ciclo**," \
    " fondato su un deciso ringiovanimento della rosa. Questa fase si rivela immediatamente vincente: il club conquista il titolo con una squadra" \
    " giovane e si conferma nelle stagioni successive, culminando nel trionfo del 2009/10, ottenuto con un’età media significativamente più alta.   \n" \
    "Sebbene i giocatori protagonisti dei titoli a inizio e fine ciclo non siano gli stessi, è evidente come il club non abbia mostrato particolare" \
    " attenzione al fattore anagrafico finché i risultati continuavano ad arrivare. Solo dopo aver raggiunto un’età media elevata si è assistito" \
    " a una nuova inversione di tendenza, segno che il **ringiovanimento è stato attivato come risposta ciclica**, piuttosto che come strategia strutturale.    \n" \
    "In generale, l’andamento suggerisce che il Chelsea abbia seguito una logica a cicli ben definiti: fasi di costruzione con età contenuta," \
    " maturità competitiva prolungata fino al picco, e successivo ricambio generazionale."
)

st.divider()


# -------------
# 3.4) Mostro i capocannonieri

st.caption("Capocannonieri tra il 2002 e il 2010")
st.dataframe(
    df_topscorer
        .slice(10, 9)  
        .select(pl.all().exclude("Anno")) 
        .to_pandas()
        .style.apply(evidenzia_squadra("Chelsea FC", "#001F5C"), axis=1),
    hide_index=True
)
st.markdown("Vediamo che il Chelsea è stata anche la squadra del capocannoniere della lega per **3 volte** (anche se non con numeri stratosferici) in questo periodo.")

st.divider()


# -------------------------
# 3.5) Mostra Dataset

if "mostra_dataset" not in st.session_state:
    st.session_state.mostra_dataset = False

if st.button("Mostra dataset"):
    st.session_state.mostra_dataset = not st.session_state.mostra_dataset

if st.session_state.mostra_dataset:

    # 1) df_age
    st.markdown("**df_age** (scraped): Età media per squadra e stagione (fonte [Transfermarkt](https://www.transfermarkt.it/premier-league/altersschnitt/wettbewerb/GB1))")
    st.dataframe(df_age.head(100), use_container_width=True)

    st.divider()

    # 2) df_topscorer
    st.markdown("**df_topscorer** (copied): Migliori marcatori per ogni stagione (Top Scorer)")
    st.dataframe(df_topscorer, use_container_width=True)
    st.markdown("**Multipli**: 1 se in quella stagione più giocatori sono stati capocannonieri a pari merito, 0 altrimenti",unsafe_allow_html=True)

    # Nascondi Dataset
    st.markdown("<br><br><br>*Per nascondere i dataset, premere due volte il pulsante.*", unsafe_allow_html=True)
    if st.button("Nascondi dataset"):
        st.session_state.mostra_dataset = False