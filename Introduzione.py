import altair as alt
import polars as pl
import streamlit as st


# ===============================
# 1. FUNZIONI FACILITATRICI
# ===============================


# 1) Funzione di caricamento dati
def carica_dati(path: str):
    return pl.read_csv(path, null_values=["", "NA ", " NA", "NA"])


# 2) Elaborazione dataset: compatibilità e ordinamento
def completa_e_ordina(df: pl.DataFrame) -> pl.DataFrame:
    """
    - Aggiunge 'Anno' o 'Stagione' se mancanti
    - Converte 'Stagione' nel formato 'YYYY/YY'
    - Forza i tipi: Anno -> Int64, Stagione -> Utf8
    - Riordina le colonne: 'Stagione', ..., 'Anno'
    """
    df_result = df.clone()

    # --- Aggiungi Anno se manca ---
    if "Anno" not in df_result.columns and "Stagione" in df_result.columns:
        df_result = df_result.with_columns(
            pl.col("Stagione")
            .str.replace_all("-", "/")
            .str.split("/")
            .list.get(0)
            .cast(pl.Int64)
            .alias("Anno")
        )

    # --- Aggiungi Stagione se manca ---
    if "Stagione" not in df_result.columns and "Anno" in df_result.columns:
        df_result = df_result.with_columns(
            (
                pl.col("Anno").cast(pl.Utf8) + "/" +
                (pl.col("Anno") + 1).cast(pl.Utf8).str.slice(-2, 2)
            ).alias("Stagione")
        )

    # --- Forza cast corretto ---
    if "Anno" in df_result.columns:
        df_result = df_result.with_columns(pl.col("Anno").cast(pl.Int64))
    if "Stagione" in df_result.columns:
        df_result = df_result.with_columns(pl.col("Stagione").cast(pl.Utf8))

    # --- Riformatta Stagione ---
    if "Anno" in df_result.columns:
        df_result = df_result.with_columns(
            (
                pl.col("Anno").cast(pl.Utf8) + "/" +
                (pl.col("Anno") + 1).cast(pl.Utf8).str.slice(-2, 2)
            ).alias("Stagione")
        )

    # --- Riordina ---
    cols = df_result.columns
    centro = [col for col in cols if col not in ("Stagione", "Anno")]
    colonne_finali = []
    if "Stagione" in cols:
        colonne_finali.append("Stagione")
    colonne_finali.extend(centro)
    if "Anno" in cols:
        colonne_finali.append("Anno")

    return df_result.select(colonne_finali)


# 3) Evidenziare una riga di dataset
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


# Caricamento dei dataset, completati e ordinati
df_principale   = carica_dati("principale.csv")
df_rankings  = carica_dati("rankings.csv")
df_record = carica_dati("record.csv")
df_perpetua  = carica_dati("perpetua.csv")


# Liverpool - preparazione
df_liverpool = (
    df_rankings
    .filter(pl.col("Squadra") == "Liverpool") 
    .select(["Stagione", "Posizione", "Punteggio", "Anno"])
    .rename({"Posizione": "Pos", "Punteggio": "Pts"})
    .sort("Anno")
    .to_pandas()
)

# Score inverso: 1° → più grande, 20° → più piccolo
max_pos = df_liverpool["Pos"].max()
df_liverpool["Score"] = (max_pos + 1) - df_liverpool["Pos"]




# ====================================================
# 3. VISUALIZZAZIONE CON STREAMLIT E Altair
# ====================================================


# -------------------------
# 3.1 Introduzione

st.markdown(
    "<h1 style='text-align: center;'> Premier League Analysis </h1>",
    unsafe_allow_html=True
)
st.image('./Premie_League_logo.jpg')
"*(please use light theme)*"
""

st.text("In questo progetto vengono presentate alcune analisi relative alle 32 stagioni della massima lega" \
" calcistica inglese dalla nascita della Premier League al 2024 (dalla stagione 1992/93 a quella 2023/24)."\
" Attraverso dataset dedicati — alcuni estratti da fonti esistenti, altri costruiti tramite script Python" \
" — ho voluto descrivere l'evoluzione del campionato inglese, soffermandomi su tendenze significative che " \
"raccontano le trasformazioni, i picchi e le cadute di alcune squadre.  \n" \
"L’analisi, oltre ad usare le statistiche di base degli incontri, come vittorie, sconfitte, goal, etc., " \
" include aspetti come l’età media delle squadre vincitrici e la presenza di un vero e proprio ‘bomber’ in rosa,")
st.divider()


# -------------------------
# 3.2 Records

st.subheader("Record storici e statistiche rilevanti")
st.text("Inizio mettendo in evidenza le stagioni più brillanti sotto il profilo statistico, premiando quelle squadre che hanno" \
" lasciato un segno per la qualità di rendimento.")
st.dataframe(df_record.slice(0,6), use_container_width=True)
st.markdown("La stagione 2017/18 del Manchester City si conferma come la più dominante della storia recente del calcio inglese," \
" va a loro il merito di aver sforato per la prima volta la **tripla cifra** nei punti ottenuti.   \n " \
"L’Arsenal, invece, può vantare un primato ineguagliato: l’unica squadra ad aver chiuso una stagione da **imbattuta**.")
st.divider()
st.text("A differenza delle performance esaltanti appena mostrate, la tabella seguente espone" \
" i risultati più deludenti ottenuti da squadre vincitrici.")
st.dataframe(df_record.slice(6,6), use_container_width=True)
st.markdown("Il Manchester United emerge (a malincuore per i suoi tifosi) come la protagonista di queste stagioni meno brillanti.   \n " \
"Notevole — e sorprendente — anche il dato relativo al Chelsea FC: ha vinto un titolo con una differenza reti inferiore" \
" al numero di partite disputate, il che significa che mediamente non ha mantenuto **nemmeno un gol di scarto per gara**.")
st.divider()
st.text("Concludo la sezione relativa ai titoli mostrando le stagioni in cui alcune squadre, pur avendo offerto prestazioni straordinarie," \
" non sono riuscite a conquistare il titolo, spesso superate da avversarie semplicemente più in forma nel momento cruciale.")
st.dataframe(df_record.slice(12,6), use_container_width=True)
st.text("In questo contesto, il Liverpool merita una menzione particolare: può essere considerata la squadra “quasi campione” " \
        "per eccellenza, più volte vicina alla vittoria senza mai riuscire a completare l’opera.")
st.divider()
st.text("Ecco infine qualche altro dato particolare, su cui però non ci dilungheremo...")
st.dataframe(df_record.slice(18,7), use_container_width=True)
st.markdown("... Se non per due dati che rivedremo in seguito...")
st.divider()


# -------------------------
# 3.3 Liverpool - grafico

# Chart base
base = alt.Chart(df_liverpool).encode(
    y=alt.Y("Stagione:O", sort=list(df_liverpool["Stagione"]), title=None),
    tooltip=[
        alt.Tooltip("Stagione:O", title="Stagione"),
        alt.Tooltip("Pos:Q", title="Posizione"),
        alt.Tooltip("Pts:Q", title="Punti")
    ]
)

# Barre per lo Score + colore in funzione dei Punti
bars = base.mark_bar().encode(
    x=alt.X(
        "Score:Q",
        title=None,
        scale=alt.Scale(domain=[0, max_pos]),
        axis=alt.Axis(
            values=list(range(20, 0)),
        )
    ),
    color=alt.Color(
        "Pts:Q",
        scale=alt.Scale(scheme="reds"),
        legend=alt.Legend(title="Punti")
    )
)

# Etichette di punti all’inizio della barra
labels_pos = base.mark_text(
    align="left",
    dx=3,
    fontSize=10
).encode(
    x=alt.value(0),  # posiziona all’inizio
    text=alt.Text("Pts:Q")
)


# Etichette di punti alla fine della barra
labels_pts = base.mark_text(
    align="left", dx=3, fontSize=10, color="black"
).encode(
    x=alt.X("Score:Q"),
    text=alt.Text("Pos:Q"),
    color=alt.condition(
        alt.datum.Pos > 4,        # se Pos ≥ 5
        alt.value("red"),         # colore rosso
        alt.value("black")        # altrimenti nero
    )
)

# Composizione finale
chart = (bars + labels_pos + labels_pts).properties(
    width=700,
    height=500,
    background="#f0f0f0",
    padding={"left":20,"right":20,"top":20,"bottom":20}
    ).configure_title(
    fontSize=16, fontWeight="bold", anchor="middle"
).configure_axis(
    labelFontSize=12, titleFontSize=14
)


st.subheader("Liverpool: Posizione e Punti per Stagione")
st.caption("La lunghezza delle barre indica la posizione finale, l'intensità del colore il numero di punti ottenuti." \
" Le posizioni in rosso sono quelle fuori dalla 'zona champions', valide per l'accesso alla Champions League")
st.altair_chart(chart, use_container_width=True)
st.markdown("Nel corso delle ultime 32 stagioni, il Liverpool ha centrato l’accesso alla Champions League in ben 20 occasioni," \
" confermandosi una delle presenze più costanti ai vertici del calcio inglese. In particolare, ha chiuso il campionato al" \
" **secondo posto per 5 volte**, sfiorando più volte il titolo e consolidando il suo status tra le big della Premier League.")

st.divider()

# -------------------------
# 3.4 Liverpool- classifica perpetua

st.text("E come ci conferma la classifica perpetua, i Reds sono nella top 3 per punti accumulati.")
st.caption("Classifica Perpetua: mostra le statistiche di gioco cumulate dalla prima stagione del 1992/93 ad oggi")
st.dataframe(df_perpetua.to_pandas().head(7).style.apply(evidenzia_squadra("FC Liverpool", "#ec0a0a"), axis=1), use_container_width=True, hide_index=True)

st.divider()


# -------------------------
# 3.5 Mostra Dataset

if "mostra_dataset" not in st.session_state:
    st.session_state.mostra_dataset = False

if st.button("Mostra dataset"):
    st.session_state.mostra_dataset = not st.session_state.mostra_dataset

if st.session_state.mostra_dataset:
    
    # 1) df_principale
    st.markdown("**df_principale** (copied and processed): Per ciascuna stagione, la squadra vincitrice e le sue statistiche")
    st.dataframe(df_principale, use_container_width=True)
    st.markdown(
        "**GF**: Goal Fatti &nbsp;&nbsp;&nbsp;&nbsp; **GS**: Goal Subiti &nbsp;&nbsp;&nbsp;&nbsp; **GD**: Goal Difference &nbsp;&nbsp;&nbsp;&nbsp; **PPG**: Points Per Game"
        "<br><br>Il dataset mostrato è stato preso dal sito "
        "[my football facts](https://it.myfootballfacts.com/premier-league/all-time-premier-league/premier-league-winners-by-year/) "
        "ed è stato poi elaborato tramite la libreria **Polars**. I dati sulle età medie sono stati integrati da df_age.",
        unsafe_allow_html=True
    )

    st.divider()

    # 2) df_rankings
    st.markdown("**df_rankings** (scraped): Classifiche e statistiche di tutte le stagioni")
    st.dataframe(df_rankings.head(100), use_container_width=True)
    st.text("Questo dataset è stato creato tramite il file “crea_rankings.py” presente nella cartella." \
    " (prime 100 righe)")

    # Nascondi Dataset
    st.markdown("<br><br><br>*Per nascondere i dataset, premere due volte il pulsante.*", unsafe_allow_html=True)
    if st.button("Nascondi dataset"):
        st.session_state.mostra_dataset = False
