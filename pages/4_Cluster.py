import altair as alt
import polars as pl
import pandas as pd
import streamlit as st
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score



# ===============================
# 1. FUNZIONE FACILITATRICI
# ===============================


# Funzione di caricamento dati
def carica_dati(path: str):
    return pl.read_csv(path, null_values=["", "NA ", " NA", "NA"])


# ===============================
# 2. OPERAZIONI DI PREPARAZIONE DEI DATASET
# ===============================


# Caricamento dei dataset
df_winners   = carica_dati("principale.csv")
df_titles    = carica_dati("titles.csv")
df_topscorer = carica_dati("top_scorer.csv")

# Mappa che associa a ogni cluster un colore esatto
color_map = {
    0: "#0140BD",
    1: "#00B1B7",
    2: "#FF0303",
    3: "#FFB3B3",
    4: "#489F85",
    5: "#2EF79D",
    6: "#F2A600",
    7: "#FCEC9F",
    8: "#9467BD",
    9: "#E7E0F2"
}


# ------------------------------
# 2.1 Costruzione dataframe con le variabili che mi interessano

df_cluster = (
    df_winners
    .join(
        df_topscorer.rename({"Squadra":"TopScorerTeam"}).select(["Anno", "TopScorerTeam"]),
        on="Anno", how="left"
    )
    .with_columns([
        (pl.col("TopScorerTeam") == pl.col("Vincitore")).cast(pl.Int64).alias("HasTopScorer")
    ])
    .select(["Stagione", "Vincitore", "Punteggio", "GF", "GS", "GD", "Vittorie", "Pareggi", "Sconfitte", "HasTopScorer", "Average_age"])
)

# Features ordinate
features = ["Punteggio", "GF", "GS", "GD", "Vittorie", "Pareggi", "Sconfitte", "HasTopScorer", "Average_age"]

# Conversione in pandas
df_cluster_pd = df_cluster.to_pandas().set_index(["Stagione", "Vincitore"])


# ------------------------------
# 2.2 Standardizzazione, Costruzione PC, KMeans dinamico

# Slider per il numero di cluster
k_clusters = st.sidebar.slider(         # metto lo slider nella sidebar
    "Numero di cluster",
    min_value=2,
    max_value=10,
    value=3,
    step=1,
    help="Seleziona quanti cluster usare per raggruppare le stagioni"
)

# Standardizzazione delle variabili
scaler = StandardScaler()
X_scaled = scaler.fit_transform(df_cluster_pd[features])

# PCA con 3 componenti
pca = PCA(n_components=3)
X_pca = pca.fit_transform(X_scaled)

# KMeans con k che varia in base allo slider
kmeans = KMeans(n_clusters=k_clusters, random_state=42)
df_cluster_pd["Cluster"] = kmeans.fit_predict(X_scaled)
df_cluster_pd[["PC1", "PC2", "PC3"]] = X_pca

# Reset index per visualizzazione
df_cluster_pd.reset_index(inplace=True)
df_cluster_pd["Cluster_label"] = df_cluster_pd["Cluster"].map(
    lambda c: f"{c}"
)


# ------------------------------
# 2.3 Bar Chart medie per cluster e unione con Z-score

# Calcolo delle medie delle variabili per cluster (valori raw)
medie_raw = (
    df_cluster_pd.groupby("Cluster")[features]
    .mean()
    .round(2)
    .reset_index()
    .melt(id_vars="Cluster", var_name="Variabile", value_name="Valore")
)

# Calcolo delle medie standardizzate (Z-score)
medie_z = (
    pd.DataFrame(X_scaled, columns=features,
                 index=df_cluster_pd.set_index(["Stagione","Vincitore"]).index)
    .assign(Cluster=df_cluster_pd['Cluster'].values)
    .groupby('Cluster')[features]
    .mean()
    .reset_index()
    .melt(id_vars='Cluster', var_name='Variabile', value_name='Z-score')
)

# Unisco le due tabelle
df_medie_scaled = (
    medie_raw
    .merge(medie_z, on=['Cluster','Variabile'], how='inner')
)



# ====================================================
# 3. VISUALIZZAZIONE CON STREAMLIT E Altair
# ====================================================


# Slider nella sidebar visualizzato nel blocco precedente


# ------------------------------
# 3.1 PCA 2D con dimensione proporzionale a PC3

chart_3d_flat = (
    alt.Chart(df_cluster_pd)
    .mark_circle() 
    .encode(
        x=alt.X("PC1", title="Dominanza (PC1)"),
        y=alt.Y("PC2", title="Età Media / Stile (PC2)"),
        size=alt.Size(
            "PC3", title=["(PC3)","Non Vittorie"], scale=alt.Scale(range=[100, 1000])  
        ),
        color=alt.Color("Cluster_label:N", title="Cluster"),
        shape=alt.Shape("Cluster_label:N"),
        tooltip=[
            "Stagione", "Vincitore", "PC3", "Punteggio",
            "GF", "Vittorie", "Sconfitte", "Average_age", "HasTopScorer"
        ]
    )
    .properties(
        width=800, height=500, background="#f0f0f0",
        title={
            "text": f"PCA (k = {k_clusters}): Dimensione proporzionale a PC3",
            "anchor": "middle", "fontSize": 20, "dx": 10, "dy": 10
        },
        padding={"left": 20, "right": 20, "top": 20, "bottom": 20}
    )
)

st.subheader("Cluster Analysis: Performance del Vincitore")
st.caption(
    "Visualizzazione della performance del vincitore di ogni campionato rispetto alle prime 3 componenti principali, "
    f"raggruppate in k = {k_clusters} cluster (k arbitrario).  \n" \
    "A dimensioni ridotte dei cerchi corrisponde un livello più basso in Sconfitte e più alto in Pareggi"
)
st.altair_chart(chart_3d_flat, use_container_width=True)
st.markdown("Questo grafico mostra i vincitori di ogni stagione proiettati sulle prime due componenti principali, con il terzo asse rappresentato" \
    " dalla dimensione dei cerchi, proporzionale al numero di pareggi (valori positivi) o sconfitte (valori negativi).  \n" \
    "Con k = 3* cluster: Il **Cluster 0 (blu)** caratterizza stagioni con dominanza intermedia, pochissime sconfitte e/o elevato numero di pareggi (PC3 molto basso);" \
    " Il **Cluster 1 (azzurro)** raccoglie le squadre con alta dominanza (PC1 >> 0) e moderate percentuali di non-vittoria;   \n" \
    " Il **Cluster 2 (rosso)** include campioni con minore dominanza e stile di gioco neutro (PC1 negativo, PC2 intorno allo 0).    \n" \
    "In sintesi, il grafico distingue chiaramente epoche di supremazia netta, cicli più equilibrati e stagioni in cui il campionato è stato deciso da pochi punti.  \n\n" \
    "**Vedere Elbow Method e Silhouette Score per capire perchè la scelta di k = 3 cluster sia la più idonea.*" \
    )

st.divider()


# ------------------------------
# 3.2  Elbow Method e Silhouette Score

# Checkbox per mostrare i plot di validazione
show_validation = st.sidebar.checkbox(
    "Mostra Elbow Method e Silhouette Score",
    value=False,
    help="Metriche per scegliere il numero idoneo di Cluster"
)

if show_validation:

    st.markdown("*Ecco perchè tutte le analisi sono state fatte su k=3 cluster...*")

    # --------------
    # Elbow Method
    inertie = []
    k_range = list(range(1, 11))
    for k in k_range:
        km = KMeans(n_clusters=k, random_state=42)
        km.fit(X_scaled)
        inertie.append(round(km.inertia_,3))

    elbow_df = pd.DataFrame({
        "k": k_range,
        "Inerzia": inertie
    })

    # Salvo il valore di SSE per k selezionato
    sse_k = elbow_df.loc[elbow_df["k"] == k_clusters, "Inerzia"].iloc[0]

    elbow_chart = (
        alt.Chart(elbow_df)
        .mark_line(point=True)
        .encode(
            x=alt.X("k:O", title="Numero di cluster (k)", axis=alt.Axis(labelAngle=0, labelFontSize=12)),
            y=alt.Y("Inerzia:Q", title="Sum of Squared Errors"),
            tooltip=["k", "Inerzia"]
        )
        .properties(
            width=600, height=350, background="#f0f0f0",
            padding={"left":20,"right":20,"top":20,"bottom":20}
        )
    )

    st.subheader("Elbow Method")
    st.caption(
        "Somma dei quadrati delle distanze interne ai cluster (SSE) in base a k (Num. di Cluster).  \n"
        "Si sceglie il k in corrispondenza del punto in cui la curva inizia ad “appiattirsi”."
    )
    st.altair_chart(elbow_chart, use_container_width=False)
    st.markdown(f"SSE per k = {k_clusters}: **{sse_k}**")
    st.text("La curva inizia a scendere con meno rapidità dal 3º o 4º cluster.")

    # --------------
    # Silhouette Score
    silhouette_scores = []
    k_range_sil = list(range(2, 11))

    for k in k_range_sil:
        km_temp = KMeans(n_clusters=k, random_state=42)
        labels_temp = km_temp.fit_predict(X_scaled)
        score = silhouette_score(X_scaled, labels_temp)
        silhouette_scores.append(round(score, 3))

    silhouette_df = pd.DataFrame({
        "k": k_range_sil,
        "Silhouette Score": silhouette_scores
    })

     # Score del numero di cluster selezionato
    score_k = silhouette_scores[k_range_sil.index(k_clusters)]

    silhouette_chart = (
        alt.Chart(silhouette_df)
        .mark_line(point=True)
        .encode(
            x=alt.X("k:O", title="Numero di cluster (k)", axis=alt.Axis(labelAngle=0, labelFontSize=12)),
            y=alt.Y("Silhouette Score:Q", title="Silhouette Score"),
            tooltip=["k", "Silhouette Score"]
        )
        .properties(
            width=600, height=350, background="#f0f0f0",
            padding={"left":20,"right":20,"top":20,"bottom":20}
        )
    )

    st.subheader("Silhouette Method")
    st.caption(
        "Silhouette Score misura quanto ciascun punto sia simile al proprio cluster rispetto a quelli vicini.\n"
        "Valori più alti indicano cluster ben separati e coerenti."
    )
    st.altair_chart(silhouette_chart, use_container_width=False)
    st.markdown(f"Silhouette Score per k = {k_clusters}: **{score_k}**")
    st.text("Vedo un grande tonfo nel valore ottenuto con 3 o con 4 cluster.")

    st.markdown("Tenendo conto di entrambi gli indici, la scelta consigliata è quindi quella di utitlizzare **3 cluster**, dato che " \
    "se scegliessi k = 4 cluster abbasserei di poco la SSE e peggiorerei parecchio il punteggio di Silhouette.  \n" \
    "Consiglio la selezione di numero di cluster = 3 per avere una corrispondenza tra descrizioni e grafici.")

    st.divider()


# ------------------------------
# 3.4 GRAFICO BAR: Media per Cluster con tutte le variabili significative

medie_chart = (
    alt.Chart(df_medie_scaled)
    .mark_bar()
    .encode(
        x=alt.X("Variabile:N", title=None),
        y=alt.Y("Valore:Q"),
        color=alt.Color("Cluster:N", title="Cluster"),
        column=alt.Column("Cluster:N", title="")
    )
    .properties(
        width=168, height=300, background="#f0f0f0",
        padding={"left": 20, "right": 20, "top": 20, "bottom": 20}
    )
)

st.subheader(f"Statistiche Medie per Cluster (k = {k_clusters})")
st.caption("Grafico a barre che mostra le medie assolute delle principali variabili per ciascun cluster di vincitori (k = 3).")
st.altair_chart(medie_chart, use_container_width=False)
st.markdown("In questo grafico è semplice individuare le variabili che caratterizzano ogni cluster, di fatti si possono confrontare le medie delle variabili" \
    " e da qui intuire facilmente un Vincitrice con dati valori dove probabilmente verrà raggruppato.   \n" \
    "Il **Cluster 0** è caratterizzato da punteggi elevati ma ottenuti attraverso molti pareggi e poche reti segnate," \
    " a fronte di pochissime sconfitte: suggerisce squadre solide ma non particolarmente offensive.     \n" \
    "Il **Cluster 1** mostra valori bilanciati: alta differenza reti, molte vittorie, bassa età media e una tendenza offensiva marcata," \
    " con frequente presenza del capocannoniere.    \n" \
    "Il **Cluster 2** rappresenta campioni meno dominanti: pur con differenza reti positiva e diversi gol segnati, evidenziano più sconfitte," \
    " meno punti complessivi e meno vittorie, lasciando intendere un titolo conquistato in contesti più equilibrati o stagioni meno brillanti."
)

st.divider()


# ------------------------------
# 3.5 GRAFICO “FRECCE” ORIZZONTALI COLORATE PER CLUSTER (COLORI DAL GRAFICO)

st.subheader(f"Statistiche Medie Standardizzate a Frecce")
st.caption("Analisi delle statistiche standardizzate (z-score) dei vincitori di campionato, suddivisi in 3 cluster.  \n" \
"Ogni freccia rappresenta di quante deviazioni standard il valore del cluster si sposta rispetto alla media su una variabile: " \
"valori positivi indicano performance superiori alla media, valori negativi inferiori.")

# Widget per selezionare quale singolo cluster plottare
cluster_sel = st.selectbox(
    "Seleziona il cluster da visualizzare",
    options=sorted(df_medie_scaled["Cluster"].unique()),
    index=0,
    format_func=lambda x: f"Cluster {x}"
)

# Filtriamo il DataFrame solo sul cluster scelto
df_sel = df_medie_scaled[df_medie_scaled["Cluster"] == cluster_sel]

# Prelevo il colore corrispondente dalla mia color map
color_sel = color_map[int(cluster_sel)]

# Costruisco il chart base su questo sottoinsieme, con i calcoli inline per x_start e x_end
base_sel = (
    alt.Chart(df_sel)
    .transform_calculate(
        # x_start = Z-score se negativo, altrimenti 0
        x_start="datum['Z-score'] < 0 ? datum['Z-score'] : 0",
        # x_end   = Z-score se positivo, altrimenti 0
        x_end="datum['Z-score'] > 0 ? datum['Z-score'] : 0"
    )
    .encode(
        y=alt.Y("Variabile:N", sort=features, title=None)
    )
)

# Regole orizzontali che vanno da x_start a x_end,
rules_sel = base_sel.mark_rule(strokeWidth=2).encode(
    x=alt.X(
        "x_start:Q",
        title="Z-score",
        scale=alt.Scale(domain=[-2.5, 2.5])
    ),
    x2="x_end:Q",
    color=alt.value(color_sel)
)

# Frecca per valori positivi (Triangolino per valori > 0) 
arrows_pos_sel = base_sel.mark_point(
    shape="triangle-right",
    size=80,
    color=color_sel
).transform_filter(
    alt.datum["Z-score"] > 0
).encode(
    x=alt.X("x_end:Q", scale=alt.Scale(domain=[-2.5, 2.5]))
)

# Frecca per valori negativi (Triangolino per valori < 0) 
arrows_neg_sel = base_sel.mark_point(
    shape="triangle-left",
    size=80,
    color=color_sel
).transform_filter(
    alt.datum["Z-score"] < 0
).encode(
    x=alt.X("x_start:Q", scale=alt.Scale(domain=[-2.5, 2.5]))
)

# Grafico Finale: unisco i layer 
chart_arrows_sel = alt.layer(rules_sel, arrows_pos_sel, arrows_neg_sel
    ).properties(
        width=600,   
        height=400, 
        background="#f0f0f0",
        padding={"left":20,"right":20,"top":20,"bottom":20}
)


# st.subheader() già visualizzato prima del selector
st.altair_chart(chart_arrows_sel, use_container_width=True)
st.markdown("Una valida alternativa al grafico precedente per capire la suddivisione in cluster delle Vincitrici è quella di vedere i valori" \
    " standardizzati al posto di quelli in scala reale: nonostante sia più difficile interpretare i risultati a colpo d'occhio, sarà più facile" \
    " notare le variazioni in media delle variabili con scala minore (come HasTopScorer, Sconfitte o Pareggi).   \n" \
    "   \nIl grafico evidenzia tre distinti profili di vittoria:     \n" \
    " - Il **Cluster 0** comprende squadre con molte partite pareggiate, pochi gol subiti e un’età media leggermente sotto la media.   \n" \
    " - Il **Cluster 1** è il più “efficiente”, con buoni punteggi, tante vittorie, e un rapporto offensivo-difensivo bilanciato.  \n" \
    " - Il **Cluster 2** rappresenta campioni atipici, con meno punti e vittorie, ma differenza reti positiva e molti pareggi.  \n\n" \
    "Questa segmentazione suggerisce che la vittoria in Premier League può derivare da approcci molto diversi:" \
    " dominio netto, equilibrio, oppure efficacia difensiva e solidità.")

st.divider()


# ------------------------------
# 3.6 Loading Componenti

# Loadings (peso delle variabili su ogni componente)
loadings_df = pd.DataFrame(
    pca.components_.T, columns=[f"PC{i+1}" for i in range(pca.n_components_)], index=features
).round(3)

st.subheader("Pesi delle Componenti Principali (Loadings)")
st.caption("Tabella che riporta i coefficienti di loadings delle variabili originali sulle tre"
    " componenti principali ottenute tramite PCA")
st.dataframe(loadings_df)
st.markdown(
    "La PC1, interpretata come asse della **“dominanza”**, è fortemente influenzata da vittorie, punteggio e differenza reti (tutti con" \
    " carichi positivi), mentre mostra un contributo negativo dai pareggi, coerente con l’idea che una squadra dominante vinca spesso e pareggi poco.    \n" \
    "La PC2 sembra riflettere lo **“stile di gioco”** e la composizione anagrafica, con alti valori associati a età media, gol fatti e" \
    " HasTopScorer (se presente aumenta il valore della seconda componente), indicando squadre più mature e offensive.  \n" \
    "Infine, la PC3 è quella più legata alla componente **“non vittorie”**: è fortemente correlata positivamente alle sconfitte, e negativamente" \
    " a HasTopScorer e pareggi, suggerendo che rappresenti un asse di instabilità o fragilità competitiva.  \n\n" \
    "Nel complesso, le componenti estratte sintetizzano in modo efficace diversi aspetti strutturali delle stagioni vincenti.   \n  \n" \
    "*Per visualizzare graficamente l'apporto delle variabili rispetto alle componenti mostrare i biplot.*"
)


# ------------------------------
# 3.7 Mostra Biplot multipli con unico toggle e size = componente rimanente 

show_biplot = st.sidebar.checkbox(
    "Mostra Biplot",
    value=False,
    help="Visualizza i biplot per tutte le combinazioni di componenti principali"
)

def make_biplot(pc_x, pc_y):
    """
    Biplot tra PC{pc_x} e PC{pc_y}, con size = la terza componente e scala ridotta
    """
    all_pcs = {1, 2, 3}
    size_pc = list(all_pcs - {pc_x, pc_y})[0]
    size_col = f"PC{size_pc}"
    x_col, y_col = f"PC{pc_x}", f"PC{pc_y}"

    comps = pca.components_.T[:, [pc_x-1, pc_y-1]]
    load_df = pd.DataFrame(comps, index=features, columns=[x_col, y_col])
    max_x, max_y = df_cluster_pd[[x_col, y_col]].abs().max()
    max_lx, max_ly = load_df.abs().max()
    scale_vec = min(max_x / max_lx, max_y / max_ly) * 0.7

    ld = load_df.reset_index().rename(columns={"index":"Variabile"})
    ld["x2"] = ld[x_col] * scale_vec
    ld["y2"] = ld[y_col] * scale_vec

    lines = []
    for _, r in ld.iterrows():
        lines.append({x_col: 0,      y_col: 0,      "Variabile": r["Variabile"]})
        lines.append({x_col: r["x2"], y_col: r["y2"], "Variabile": r["Variabile"]})
    lines_df = pd.DataFrame(lines)

    pts = (
        alt.Chart(df_cluster_pd)
        .mark_circle(opacity=0.7)
        .encode(
            x=alt.X(f"{x_col}:Q", title=x_col),
            y=alt.Y(f"{y_col}:Q", title=y_col),
            size=alt.Size(
                f"{size_col}:Q",
                legend=alt.Legend(title=size_col),
                scale=alt.Scale(range=[50, 500])  
            ),
            color=alt.Color("Cluster_label:N", title="Cluster"),
            tooltip=["Stagione", "Vincitore", "Cluster_label", alt.Tooltip(f"{size_col}:Q", format=".3f", title=size_col)]
        )
    )

    vec = (
        alt.Chart(lines_df)
        .mark_line(strokeWidth=2, color="black", opacity=0.8)
        .encode(
            x=alt.X(f"{x_col}:Q"),
            y=alt.Y(f"{y_col}:Q"),
            detail="Variabile:N"
        )
    )
    lbl = (
        alt.Chart(ld)
        .mark_text(dx=5, dy=-5, fontSize=12, fontWeight="bold")
        .encode(x="x2:Q", y="y2:Q", text="Variabile:N")
    )

    return (
        alt.layer(vec, pts, lbl)
        .properties(
            width=600, height=450, background="#f0f0f0",
            padding={"left":20,"right":20,"top":10,"bottom":10},
            title={
              "text": f"Biplot PCA ({x_col} vs {y_col}) con size = PC{size_pc}",
              "anchor": "middle",        
              "fontSize": 18
              }
        )
        .configure_axis(grid=True, gridOpacity=0.3)
    )

if show_biplot:
    st.subheader("Biplot multipli delle componenti principali")
    st.caption(
    "Biplot delle componenti principali con proiezione delle osservazioni (stagioni vincenti) e delle variabili originali.  \n" \
    "Gli assi mostrano le combinazioni lineari delle variabili (PC1, PC2, PC3), mentre la dimensione dei punti rappresenta la terza componente." \
    " I vettori indicano direzione e intensità del contributo delle variabili originali."
    )
    st.altair_chart(make_biplot(1, 2), use_container_width=True)
    st.altair_chart(make_biplot(1, 3), use_container_width=True)
    st.altair_chart(make_biplot(2, 3), use_container_width=True)
    st.markdown(
        "Nei biplot, la separazione tra cluster è ben visibile nel piano PC1–PC2 e PC1-PC3, ma meno marcata nel grafico PC2-PC3.  \n" \
        "Questo è dovuto al fatto che seconda e terza componente spiegano una porzione minore della varianza totale e rappresentano dimensioni" \
        " più sottili (es. sconfitte, instabilità), meno determinanti nel distinguere nettamente i gruppi.  \n" \
        "Le frecce aiutano a interpretare l’influenza relativa delle variabili: più sono lunghe, maggiore è l’importanza nella costruzione degli assi.  \n" \
        "I cluster si distribuiscono in maniera coerente lungo gli assi principali: il **Cluster 1 (azzurro)** è caratterizzato da valori elevati lungo PC1," \
        " si posiziona invece in modo più contenuto su PC2 e PC3; il **Cluster 2 (rosso)** mostra valori negativi su PC1 e valori elevati su PC2 e PC3," \
        " suggerendo stagioni meno dominanti ma con caratteristiche più marcate su stile ed età media; ed" \
        " infine il **Cluster 0 (blu scuro)** occupa posizioni più centrali su PC1, ma varia significativamente lungo PC2 e PC3, indicando una maggiore" \
        " eterogeneità, specialmente per le variabili legate alla stabilità e all’irregolarità (es. sconfitte)."
    )

st.divider()


# ------------------------------
# 3.8 Varianza Spiegata 

# Percentuale di varianza spiegata
explained_var = pd.DataFrame({
    "Componente": [f"PC{i+1}" for i in range(pca.n_components_)],
    "Varianza Spiegata (%)": (pca.explained_variance_ratio_ * 100).round(2)
})

# Calcolo della varianza spiegata totale (sommando le singole percentuali)
total_varianza = explained_var["Varianza Spiegata (%)"].sum().round(2)

st.subheader("Varianza Spiegata dalle Componenti")
st.caption("Tabella della varianza spiegata (in percentuale) dalle prime tre componenti principali.")
st.dataframe(explained_var, hide_index=True)
st.markdown(f"Viene spiegata quindi il **{total_varianza}** % della varianza totale.  \n" \
    "È un risultato piuttosto soddisfacente, le prime tre componenti catturano gran parte delle informazioni chiave"
    " (dominanza, età media/stile, non vittorie), garantendo una riduzione dimensionale efficace senza perdere eccessivi dettagli."
)

st.divider()


# -------------------------
# 3.9 Mostra Dataset

if "mostra_dataset" not in st.session_state:
    st.session_state.mostra_dataset = False

if st.button("Mostra dataset"):
    st.session_state.mostra_dataset = not st.session_state.mostra_dataset

if st.session_state.mostra_dataset:

    # 1) df_cluster
    st.markdown("**df_cluster** (crafted): dataframe utilizzato per la clustering analysis, contiene index e feature")
    st.dataframe(df_cluster, use_container_width=True)

    st.divider()

    # 2) df_medie_scaled
    st.markdown("**df_medie_scaled** (crafted): contiene il valore medio e il valore medio normalizzato delle variabile per i 3 Cluster")
    st.dataframe(df_medie_scaled, use_container_width=True, hide_index= True)
    
    # Nascondi Dataset
    st.markdown("<br><br><br>*Per nascondere i dataset, premere due volte il pulsante.*", unsafe_allow_html=True)
    if st.button("Nascondi dataset"):
        st.session_state.mostra_dataset = False