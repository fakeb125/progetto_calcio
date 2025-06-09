# FILE data scraping e lavorazione dati, creazione di un dataframe con dati tidy

import requests
from bs4 import BeautifulSoup
import polars as pl
import time

def get_table(url, anno):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    response = requests.get(url, headers=headers)   # Uso requests per ottenere il contenuto
    if response.status_code // 100 != 2:    #verifico che la risposta sia positiva (code 200, 201, 202,...)
        print(f"!! errore !!, codice di risposta numero: {response.status_code}") 
    else:
        soup = BeautifulSoup(response.content, "html.parser")   #accedo al contenuto della pagina
        box = soup.find_all('table')[1]     #trovo la tabella giusta
        box_titles = box.find_all('th')     #trovo tutte le intestazioni della mia tabella
        clean_titles = [title.text.strip() for title in box_titles[1:]] + ["Anno"]
        #pulisco e colleziono in una lista le variabili (salto la prima "wappen"), inoltre aggiungo la feature "anno"
        box_rows = box.find_all('tr') #trovo tutte le righe della tabella
        clean_rows = []
        for row in box_rows[1:]:
            row_data = row.find_all('td')   #trovo i valori contenuti nella riga
            individual_data = [data.text.strip() for data in row_data[1:]] + [str(anno)] #i dati puliti di ogni riga con l'anno
            clean_rows.append(individual_data)
        df = pl.DataFrame(clean_rows, schema=clean_titles, orient="row") #colleziono in formato Polars.DataFrame i dati della stagione
    return df


if __name__ == "__main__":
    all_data = []   #inizializzo una lista che conterrà i vari DataFrames
    for anno in range(1992, 2024): 
        url = f"https://www.transfermarkt.it/premier-league/altersschnitt/wettbewerb/GB1/plus/?saison_id={anno}"
        all_data.append( get_table(url, anno) )     #aggiungo ad una lista il dataframe ottenuto da ogni stagione
        print(f"Dati per l'anno {anno} aggiunti al dataset.")
        time.sleep(2)   #aggiungo un ritardo per evitare mi venga bocciata la richiesta di accesso
    average_age = pl.concat(all_data)   #concateno i vari DataFrames in modo da ottenerne uno completo
    average_age = average_age.rename({"ø-età per partita": "Average_age"}   #semplifico il nome della feature
                ).with_columns(pl.col("Average_age").str.replace(",", ".").cast(pl.Float64))    #rendo il valore età media di tipo float64

    file_path = "average_age_copia.csv"   #percorso del file che voglio creare
    average_age.write_csv(file_path)    #salvo il file in locale 