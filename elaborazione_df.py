import altair as alt
import polars as pl
import pandas as pd


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


# 3.1) df_record -  estrazione record da dataset 

def estrai_record(df: pl.DataFrame,
                  record_nome: str,
                  col_valore: str,
                  desc: bool = True,
                  filtro: pl.Expr | None = None,
                  squad_col: str | None = None,
                  stagione_col: str | None = None) -> pl.DataFrame:
    
    # Autodetect di possibili nomi delle variabili "Squadra | Vincitrice" e "Anno | Stagione"
    if squad_col is None:
        squad_col = "Squadra"   if "Squadra"   in df.columns else \
                    "Vincitore" if "Vincitore" in df.columns else None
    if stagione_col is None:
        stagione_col = "Stagione" if "Stagione" in df.columns else \
                       "Anno"     if "Anno"     in df.columns else None
    if squad_col is None or stagione_col is None:
        raise ValueError("Impossibile determinare le colonne squadra/stagione")
    
    q = df if filtro is None else df.filter(filtro)

    riga = (
        q.sort(col_valore, descending=desc)
          .select([
              pl.lit(record_nome).alias("Record"),
              pl.col(squad_col).alias("Squadra"),
              pl.col(stagione_col).alias("Stagione"),
              pl.col(col_valore).alias("Valore")
          ])
          .limit(1)
    ).with_columns([
        pl.col("Record").cast(pl.Utf8),
        pl.col("Squadra").cast(pl.Utf8),
        pl.col("Stagione").cast(pl.Utf8),    
        pl.col("Valore").cast(pl.Float64)     
    ])
    return riga


# 3.2) df_record - formattazione

def formatta_record(r: pl.DataFrame) -> pl.DataFrame:
    """
    Garantisce uniformità: cast delle colonne, ordine, nomi coerenti.
    """
    return (
        r.with_columns([
            pl.col("Record").cast(pl.Utf8),
            pl.col("Squadra").cast(pl.Utf8),
            pl.col("Stagione").cast(pl.Utf8),
            pl.col("Valore").cast(pl.Float64)
        ])
        .select(["Record", "Squadra", "Stagione", "Valore"])
    )


# ====================================================
# 2. OPERAZIONI DI PREPARAZIONE DEI DATASET
# ====================================================


# Caricamento dei dataset, completati e ordinati
df_winners   = completa_e_ordina(carica_dati("winners.csv"))     #dataset trovato
df_average   = completa_e_ordina(carica_dati("average_age.csv"))   #dataset creato    <-- average_age_copia.csv per usare il file generato da crea_average_age
df_topscorer = completa_e_ordina(carica_dati("top_scorer.csv"))     #dataset trovato
df_rankings  = completa_e_ordina(carica_dati("rankings.csv"))    #dataset creato       <-- rankings_copia.csv


# Salvo le modifiche ai dataframe
df_average.write_csv("average_age.csv")     # aggiorno df_average
df_topscorer.write_csv("top_scorer.csv")     # aggiorno df_topscorer
df_rankings.write_csv("rankings.csv")     # aggiorno df_rankings


# -------------------------------
# 2.1 Creazione di df_principale, salvato in cartella

# Calcolo della media dell'età in lega per ciascun anno
df_league_avg = (
    df_average
    .group_by("Anno")
    .agg(pl.col("Average_age").mean().round(1).alias("League_average_age"))
)

# Unisco la media della lega in df_winners utilizzando "Anno"
df_winners = df_winners.join(
    df_league_avg,
    left_on="Anno",
    right_on="Anno",
    how="left"
)

#  Aggiunta dell'età media del vincitore da df_average
df_principale = completa_e_ordina(
    df_winners.join(
    df_average.select(["Squadra", "Anno", "Average_age"]),
    left_on=["Vincitore", "Anno"],
    right_on=["Squadra", "Anno"],
    how="left"
)
)

df_principale.write_csv("principale.csv")   # <-- salvo df_principale


# -------------------------------
# 2.2 Creazione di df_titles, salvato in cartella

# Ordinando per "Anno" e usando "pl.arange()" come contatore progressivo
df_titles = (
    df_principale
    .sort("Anno")
    .with_columns(
        (pl.arange(0, pl.count()).over("Vincitore") + 1).alias("Titoli")
    )
    .select(["Stagione", "Anno", "Vincitore", "Titoli"])
    .pipe(completa_e_ordina)
)

df_titles.write_csv("titles.csv")   # <-- salvo df_titles


# -------------------------------
# 2.4 Estrazione dei Record

records: list[pl.DataFrame] = []

# --- Record di merito
records += [
    estrai_record(df_principale, "TITOLO CON PIÙ PUNTI",     "Punteggio"),
    estrai_record(df_principale, "MIGLIOR PPG",              "PPG"),
    estrai_record(df_principale, "TITOLO CON PIÙ VITTORIE",  "Vittorie"),
    estrai_record(df_principale, "TITOLO CON MENO SCONFITTE","Sconfitte", desc=False),
    estrai_record(df_principale, "TITOLO CON PIÙ GF",        "GF"),
    estrai_record(df_principale, "TITOLO CON MIGLIOR GD",    "GD")
]

# --- Record di demerito
records += [
    estrai_record(df_principale, "TITOLO CON MENO PUNTI",    "Punteggio", desc=False),
    estrai_record(df_principale, "PEGGIOR PPG",              "PPG", desc=False),
    estrai_record(df_principale, "TITOLO CON MENO VITTORIE", "Vittorie", desc=False),
    estrai_record(df_principale, "TITOLO CON PIÙ SCONFITTE", "Sconfitte"),
    estrai_record(df_principale, "TITOLO CON MENO GF",       "GF", desc=False),
    estrai_record(df_principale, "TITOLO CON PEGGIOR GD",    "GD", desc=False)
]

# --- Record non vincitrici
non_champ = pl.col("Posizione") != 1
records += [
    estrai_record(df_rankings, "NON TITOLO CON PIÙ PUNTI",     "Punteggio", filtro=non_champ),
    estrai_record(df_rankings, "MIGLIOR PPG SENZA TITOLO",     "PPG",       filtro=non_champ),
    estrai_record(df_rankings, "NON TITOLO CON PIÙ VITTORIE",  "Vittorie",  filtro=non_champ),
    estrai_record(df_rankings, "NON TITOLO CON MENO SCONFITTE","Sconfitte", desc=False, filtro=non_champ),
    estrai_record(df_rankings, "NON TITOLO CON PIÙ GF",        "GF",        filtro=non_champ),
    estrai_record(df_rankings, "NON TITOLO CON MIGLIOR GD",    "GD",        filtro=non_champ)
]

# --- Record età
records += [
    estrai_record(df_average, "SQUADRA PIÙ VECCHIA",         "Average_age"),
    estrai_record(df_average, "SQUADRA PIÙ GIOVANE",         "Average_age", desc=False),
    estrai_record(df_principale, "VINCITRICE PIÙ VECCHIA",      "Average_age"),
    estrai_record(df_principale, "VINCITRICE PIÙ GIOVANE",      "Average_age", desc=False)
]

# --- Capocannonieri
records += [
    estrai_record(df_topscorer, "MIGLIOR CAPOCANNONIERE",  "Gol"),
    estrai_record(df_topscorer, "PEGGIOR CAPOCANNONIERE",  "Gol", desc=False)
]

# --- Squadra con più capocannonieri
squad_most_scorers = (
    df_topscorer.group_by("Squadra").count()
               .sort("count", descending=True)
               .select([
                   pl.lit("SQUADRA MAGGIOR VOLTE CON CAPOCANNONIERE").alias("Record"),
                   pl.col("Squadra"),
                   pl.lit("-").alias("Stagione"),
                   pl.col("count").alias("Valore")
               ])
               .limit(1)
)
records.append(squad_most_scorers)

# --- Concatenazione finale
df_record = pl.concat([formatta_record(r) for r in records])

df_record.write_csv("record.csv")   # <-- salvo df_record
