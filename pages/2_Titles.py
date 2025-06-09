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


# ====================================================
# 2. OPERAZIONI DI PREPARAZIONE DEI DATASET
# ====================================================


# Caricamento dei dataset
df_winners   = carica_dati("principale.csv")
df_rankings  = carica_dati("rankings.csv")
df_titles  = carica_dati("titles.csv")

# Codici associati ai colori sociali delle squadre
colori_sociali = {
    "Blackburn Rovers": "#FFFFFF",    #"bianco"
    "Chelsea FC": "#001F5C",    #"blu scuro"
    "FC Arsenal": "#ff4b4b",    #"rosso"
    "FC Liverpool": "#ec0a0a",   #"rosso chiaro"
    "Leicester City": "#005BAB",    #"blu chiaro"
    "Manchester City": "#6CABDD",    #"azzurro"
    "Manchester United": "#C50000"   #"rosso scuro"
    }


# ====================================================
# 3. VISUALIZZAZIONE CON STREAMLIT E Altair
# ====================================================


# 3.1 Grafico a barre: Titoli cumulativi

hover_selection = alt.selection_single(
    fields=["Vincitore"],  
    on="mouseover",  
    empty="all",  
    clear="mouseout" ,
    nearest=False
)
titles_bar = alt.Chart(
    df_titles.to_pandas()
).mark_bar(
    stroke='black', strokeWidth=0.3 
).encode(
    x=alt.X(
        'Anno:O', 
        title=None,
        axis=alt.Axis(labelAngle=-45)  
    ),
    y=alt.Y(
        'Titoli:Q', 
        title=None,
        scale=alt.Scale(domain=[0, df_titles['Titoli'].max() + 1]) 
    ), 
   tooltip=['Vincitore', 'Stagione', 'Titoli'], 
    color=alt.Color(
        "Vincitore:N",
        scale=alt.Scale(
            domain=list(colori_sociali.keys()),  
            range=list(colori_sociali.values()) 
        )
    ).legend(
        title="Squadre",
        symbolStrokeWidth=0.3,
        symbolSize=100,
        labelFontSize=12,
        titleFontSize=14
        ),
    opacity=alt.condition(
        hover_selection, 
        alt.value(1), 
        alt.value(0.3) 
    )
).properties(
    height=400,
    width=800,
    background='#f0f0f0', 
    padding={"left": 20, "right": 20, "top": 20, "bottom": 20}  
).configure_view(
    strokeWidth=0  
).configure_axis(
    labelFontSize=14,  
    titleFontSize=16,  
    grid=False         
).add_selection(hover_selection)


st.subheader("Evoluzione Temporale dei Trofei")
st.caption(
    "Conteggio cumulativo dei trofei per ogni anno.  \n"
    "Avvicinarsi lentamente alla stagione di interesse. Sconsiglio di scorrere velocemente tra le barre (nearest=True fallava)."
)
st.altair_chart(titles_bar, use_container_width=True)

st.divider()


# ---------------------------
# 3.2 Grafico a torta: Distribuzione dei titoli per intervallo di anni

st.subheader("Distribuzione Titoli per Intervallo di Anni")
st.caption("Passare il puntatore su uno spicchio per vederne la percentuale")


# Imposto i limiti per lo slider in base alla colonna "Anno" di df_titles
min_anno_val = int(df_titles["Anno"].min())
max_anno_val = int(df_titles["Anno"].max())

min_anno, max_anno = st.slider(
    "Seleziona l'intervallo di anni:",
    min_value=min_anno_val,
    max_value=max_anno_val,
    value=(min_anno_val, max_anno_val),
    step=1
)

# Filtraggio dei dati in base allo slider (utilizzo "Anno" in df_winners)
df_filtrato = df_winners.filter(
    (pl.col("Anno") >= min_anno) & (pl.col("Anno") <= max_anno)
)
df_pie = (
    df_filtrato.group_by("Vincitore")
    .agg(pl.count().alias("Totale_Titoli"))
    .with_columns([
        ((pl.col("Totale_Titoli") / pl.col("Totale_Titoli").sum()) * 100).alias("Percentuale"),
        (((pl.col("Totale_Titoli") / pl.col("Totale_Titoli").sum()) * 100)
         .round(1)
         .cast(pl.Utf8) + "%").alias("Percentuale_str")
    ])
)

selection = alt.selection_single(fields=["Vincitore"], on="mouseover", empty="all")

pie_chart = alt.Chart(df_pie.to_pandas()).mark_arc(
    innerRadius=70,
    outerRadius=150,
    stroke="black",
    strokeWidth=0.5
).encode(
    theta=alt.Theta("Totale_Titoli:Q", title="Numero di Titoli"),
    color=alt.Color(
        "Vincitore:N", title="Squadra Vincente",
        scale=alt.Scale(
            domain=["Blackburn Rovers", "Chelsea FC", "FC Arsenal", "FC Liverpool",
                    "Leicester City", "Manchester City", "Manchester United"],
            range=["#FFFFFF", "#001F5C", "#ff4b4b", "#ec0a0a", "#005BAB", "#6CABDD", "#C50000"]
        )
    ),
    opacity=alt.condition(selection, alt.value(1), alt.value(0.3)),
    tooltip=[
        alt.Tooltip("Vincitore:N", title="Squadra"),
        alt.Tooltip("Totale_Titoli:Q", title="Titoli vinti", format=".0f"),
        alt.Tooltip("Percentuale_str:N", title="Percentuale")
    ]
).add_selection(
    selection
).properties(
    padding={"left": 20, "right": 20, "top": 20, "bottom": 20},
    background='#f0f0f0',
    width=600,
    height=450
).configure_view(
    strokeWidth=0
).configure_legend(
    symbolStrokeWidth=0.3,
    symbolSize=100,
    labelFontSize=14,
    titleFontSize=16
).configure_title(
    anchor="middle",
    fontSize=16,
    fontWeight="bold",
    color="black"
)


st.altair_chart(pie_chart, use_container_width=True)


st.markdown("I grafici rappresentano la distribuzione e l’evoluzione temporale dei titoli in Premier League.    \n " \
"Nel primo, si osserva la crescita del numero di trofei conquistati stagione dopo stagione dalle squadre vincitrici:" \
" spiccano il **dominio** del Manchester United nei primi anni e l’ascesa del Manchester City nell’ultimo decennio.     \n" \
"Nel secondo grafico, un diagramma ad anello mostra la ripartizione percentuale dei titoli per squadra:" \
" l’ampiezza visiva rende immediatamente percepibile la superiorità storica di alcune squadre rispetto ad altre," \
" con **United** e **City** che si dividono quasi metà dell’intera torta.")


st.divider()


# ---------------------------
# 3.3 Grafico Andamento Posizioni Manchester
# ---------------------------

# 1) Prepara il DataFrame
df_lines = (
    df_rankings
    .filter(pl.col("Squadra").is_in(["Manchester Utd.", "Manchester City"]))
    .with_columns(
        pl.col("Anno").cast(pl.Utf8).alias("Stagione"),
        pl.col("Anno").alias("Anno")
    )
    .select(["Stagione", "Squadra", "Posizione", "Anno"])
    .to_pandas()
)

# 2) Selector per l’hover
hover = alt.selection_single(
    fields=["Stagione"], nearest=True,
    on="mouseover", empty="none", clear="mouseout"
)

# 3) layer invisibile + lookup per recuperare in tooltip entrambe le posizioni
rect_hover = (
    alt.Chart(df_lines)
      .transform_filter(alt.datum.Squadra == "Manchester Utd.")
      .transform_lookup(
         lookup="Stagione",
         from_=alt.LookupData(
             data=df_lines[df_lines["Squadra"]=="Manchester City"],
             key="Stagione",
             fields=["Posizione"]
         ),
         as_=["CityPosizione"]
      )
      .mark_rect(opacity=0)
      .encode(
          x="Stagione:O",
          tooltip=[
            alt.Tooltip("Stagione:O"),
            alt.Tooltip("Posizione:Q", title="Manchester United"),
            alt.Tooltip("CityPosizione:Q", title="Manchester City")
          ]
      )
      .add_selection(hover)
)

# 4) barra verticale grigia all’hover
hover_rule = (
    alt.Chart(df_lines)
      .mark_rule(color="gray", strokeWidth=1)
      .encode(
          x="Stagione:O",
          opacity=alt.condition(hover, alt.value(1), alt.value(0))
      )
      .add_selection(hover)
)

# 5) cerchi che evidenziano entrambe le squadre all’hover
hover_circles = (
    alt.Chart(df_lines)
      .mark_circle(size=100)
      .encode(
          x="Stagione:O",
          y="Posizione:Q",
          color=alt.Color("Squadra:N",
            scale=alt.Scale(
              domain=["Manchester Utd.","Manchester City"],
              range=["#C50000","#6CABDD"]
            ),
            legend=None
          ),
          opacity=alt.condition(hover, alt.value(1), alt.value(0))
      )
      .transform_filter(hover)
)

# 6) Base chart con x ordinal
base = alt.Chart(df_lines).encode(
    x=alt.X("Stagione:O", title=None, axis=alt.Axis(labelAngle=-45))
)

# 7) Bande fisse e rule tratteggiate
stg_ord = sorted(df_lines["Stagione"].unique())

top4_band = (
    alt.Chart(pd.DataFrame({"Stagione": stg_ord}))
    .mark_rect(color="silver", opacity=0.4)
    .encode(x="Stagione:O", y=alt.value(0), y2=alt.value(55))
)
euro_band = (
    alt.Chart(pd.DataFrame({"Stagione": stg_ord}))
    .mark_rect(color="silver", opacity=0.2)
    .encode(x="Stagione:O", y=alt.value(55), y2=alt.value(99))
)
rule2008 = alt.Chart(pd.DataFrame({"Stagione": ["2008"]})) \
    .mark_rule(color="#90ee90", strokeDash=[4,4], strokeWidth=2) \
    .encode(x="Stagione:O")
rule2012 = alt.Chart(pd.DataFrame({"Stagione": ["2012"]})) \
    .mark_rule(color="#FFD700", strokeDash=[4,4], strokeWidth=2) \
    .encode(x="Stagione:O")

# 8) Layer continuity + pre/post
baseline_united = base.transform_filter(alt.datum.Squadra=="Manchester Utd.") \
    .mark_line(color="#C50000", strokeWidth=2.3) \
    .encode(y=alt.Y("Posizione:Q", scale=alt.Scale(domain=[1,20], reverse=True)))
baseline_city = base.transform_filter(alt.datum.Squadra=="Manchester City") \
    .mark_line(color="#6CABDD", strokeWidth=2.3) \
    .encode(y="Posizione:Q")

united_pre = base.transform_filter((alt.datum.Squadra=="Manchester Utd.") & (alt.datum.Anno<2012)) \
    .mark_line(color="#C50000", strokeWidth=3) \
    .encode(y="Posizione:Q")
united_post = base.transform_filter((alt.datum.Squadra=="Manchester Utd.") & (alt.datum.Anno>=2012)) \
    .mark_line(color="#FFD700", strokeWidth=3) \
    .encode(y="Posizione:Q")
city_pre = base.transform_filter((alt.datum.Squadra=="Manchester City") & (alt.datum.Anno<2008)) \
    .mark_line(color="#6CABDD", strokeWidth=3) \
    .encode(y="Posizione:Q")
city_post = base.transform_filter((alt.datum.Squadra=="Manchester City") & (alt.datum.Anno>=2008)) \
    .mark_line(color="#90ee90", strokeWidth=3) \
    .encode(y="Posizione:Q")

# 9) Etichette finali
last_pos = (
    df_lines
    .sort_values("Anno")
    .groupby("Squadra")
    .tail(1)
)
final_labels = alt.Chart(last_pos).mark_text(
    align="left", dx=5, dy=5, fontSize=12, fontWeight="bold"
).encode(
    x="Stagione:O",
    y="Posizione:Q",
    text=alt.Text("Posizione:Q"),
    color=alt.Color("Squadra:N",
      scale=alt.Scale(
        domain=["Manchester Utd.","Manchester City"],
        range=["#FFD700","#90ee90"]
      ), legend=None
))

# 10) Combina tutto
chart = (
    rect_hover
  + hover_rule
  + hover_circles
  + top4_band
  + euro_band
  + rule2008
  + rule2012
  + baseline_city
  + baseline_united
  + united_pre
  + united_post
  + city_pre
  + city_post
  + final_labels
).properties(
    width=800, height=400,
    background="#f0f0f0",
    padding={"left":20,"right":20,"top":20,"bottom":20},
).configure_axis(
    labelFontSize=14
).configure_axisY(
    title=None
).configure_title(
    fontSize=16, fontWeight="bold", anchor="middle"
)


st.subheader("Andamento posizioni: Rivalità di Manchester")
st.caption("Verde: Abu Dhabi United Group acquista il Manchester city - Giallo: Ferguson non è più il coach del Manchester United")
st.altair_chart(chart, use_container_width=True)


st.markdown("Dal 1992 fino al 2013 si può parlare a tutti gli effetti di **“Era Ferguson”**: in questo periodo il Manchester United" \
" non è mai sceso oltre il terzo posto in classifica, dominando il campionato e rappresentando una costante ai vertici della Premier League." \
" Il ritiro di Sir Alex Ferguson, al termine della stagione 2012/13, segna l’inizio di un forte declino per lo United," \
" che nelle stagioni successive manca spesso la qualificazione alla Champions League e **non conquista più titoli nazionali**.")

st.markdown("Il Manchester City, al contrario, non ha mai rappresentato una reale minaccia per i vertici del campionato fino al 2008," \
" anno dell’acquisizione da parte dell’Abu Dhabi United Group. Da quel momento ha inizio una **rapida ascesa**: nel giro di poche stagioni" \
" il club scala la classifica, consolidandosi stabilmente nelle prime posizioni. La crescita è stata rapida e sostenuta," \
" fino a trasformarsi in **uno dei progetti sportivi più vincenti** del calcio inglese contemporaneo.")

st.divider()


# -------------------------
# 3.5 Mostra Dataset

if "mostra_dataset" not in st.session_state:
    st.session_state.mostra_dataset = False

if st.button("Mostra dataset"):
    st.session_state.mostra_dataset = not st.session_state.mostra_dataset

if st.session_state.mostra_dataset:

    # 1) df_titles
    st.markdown("**df_titles** (crafted): Tiene conto del numero totale di titoli vinti")
    st.dataframe(df_titles, use_container_width=True)
    st.text("")
  
    # Nascondi Dataset
    st.markdown("<br><br><br>*Per nascondere i dataset, premere due volte il pulsante.*", unsafe_allow_html=True)
    if st.button("Nascondi dataset"):
        st.session_state.mostra_dataset = False