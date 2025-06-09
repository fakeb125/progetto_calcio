
PER VISUALIZZARE IL PROGETTO È SUFFICIENTE FARE  <<     uv run streamlit run Introduzione.py    >> 

SCOPO E MOTIVO DEL PROGETTO:
L'argomento è stato scelto per passione ed interesse nella materia, nonostante la difficoltà nel reperire dati "facili" e in larga scala.
Non mi sono soffermato sull'analisi delle performance di una singola squadra o giocatore in una singola competizione tramite utilizzo di metriche recenti, come gli expected goals o le heatmap dei GPS dati ai giocatori, in quanto non sarei stato in grado di trovare dataset.
Inizialmente ero interessato a studiare come si evolvesse (e se fosse un fattore determinante) l'età media della squadra, dato che sempre più si sente di nuove star appena diciottenni. Volevo quindi verificare la mia ipotesi che l'età media delle squadre o delle vincitrici stesse calando, provando a tracciare la time series della lega in cerca di trend temporali.
Altro oggetto di interesse era l'evoluzione del centravanti boa nelle squadre, la classica punta "vecchio stampo" che ai tempi non poteva mancare e che sta pian piano venendo sostituita da altri tipi di giocatori (basti vedere l'evoluzione degli attaccanti della nazionale italiana), analisi che purtroppo non sono riuscito ad analizzare appieno per la complessità delle analisi e la mancanza di dati richiesti.
Il progetto è volto quindi verso un'analisi descrittiva dell'evoluzione di titoli ottenuti, una lezione di storia della Premier League, mantenendo comunque una parte di analisi grafica dell'età media delle squadre e mantenendo in considerazione, a tratti, il top scorer della lega.
Mi sono soffermato sullo scoprire delle chicche nascoste nel corso degli anni, per prendere coscenza di ciò che è stata e ciò che è ora il campionato inglese.
Sarebbe stato interessante anche un forecast di come potrebbe evolversi sotto questi aspetti, soprattutto le età medie, ma non ritengo di avere le competenze e gli strumenti per andare così a fondo.
Per rendere l'analisi visivamente chiara e coinvolgente, sono stati utilizzati i colori sociali delle squadre, cercando comunque di differenziarli e rendere riconoscibile la squadra in base al colore.

STRUTTURA DEL PROGETTO:
Ho diviso il progetto in più pagine, ciascuna dedicata ad un argomento di analisi, in modo da guidare al meglio l'utente nella visualizzazione e per orientarmi meglio nella scrittura del codice. Ciascuna pagina, con un titolo che già fa capire l'argomento, è riempita con grafici con una caption che spiega come debbano essere interpretati e una descrizione che ne analizza il contenuto.
All'interno del codice ho cercato di mantenere pulizia e ordine, dividendo (in ogni pagina) la parte di data processing da quella di visualizzazione.

DATI:
Sono riuscito a ricavare due dataset tramite scraping (file con spiegazioni presenti nella cartella), mentre gli altri sono stati copiati o costruiti manualmente a partire dai precedenti dataset.
ottenuti. Le variabili all'interno di tali dataset sono molto semplici: principlamente sono le classiche statistiche che si vedono in una classifica di un campionato di calcio, senza particolari variabili complesse.
I dataset utilizzati sono comunque esposti alla fine di ogni pagina, e se in questi sono presenti sigle particolari o se sono di difficile interpretazione ho scritto al di sotto anche una piccola spiegazione.
Il processing principale fatto su tutti i dataset è stato quello di controllare ed eventualmente aggiungere che ogni dataset avesse la colonna "Stagione" con un valore Utf8 utile per la visualizzazione e una colonna 'doppione' denominata "Anno" con un valore Int64 in modo da rendere più pratiche le operazioni nel codice.
Anche le fonti sono citate sul progetto, in ogni caso non sono mai stati scaricati dataset, al massimo sono stati copiati ed eleborati manualmente su excel (per esempio la costruzione delle tabella sui migliori risultati).
**Elenco dataset:**
- winners.csv : Il dataset contenente la tabella copiata dal sito my_football_facts (link in in Introduzione.py); dataset che non verrà poi mai caricato nel progetto in quanto prima passa da elaborazione_df.py e, dopo l'aggiunta della colonna sull'età media della lega e del vincitore, diventa principale.csv;
- principale.csv : Dataset che esce appunto dall'elaborazione, contiene le statistiche dei vincitori, con dati sulle età, vittorie, goal,...;
- rankings.csv : Statistiche base (vitt., goal,...) di tutte le squadre di ogni competizione;
- average_age.csv : Continene i valori delle età medie di tutte le squadre di tutte le stagioni;
- top_scorer.csv : Capocannoniere con squadra e numero di goal. Il valore multipli è stato aggiunto dal sottoscritto per evitare di avere 3 righe di capocannonieri per una stagione, ho scelto di lasciare il nome di un giocatore della squadra vincitrice se presente tra i vari co-capocannonieri.
- titles.csv : Colleziona per ogni stagione il vincitore e il numero di titoli accumulati da quella squadra fino a quell'anno;
- record.csv : Creata tramite elaborazione_df.py, ho costruito la colonna con i record ed estratto i valori tramite sorting ed estrazione dagli altri dataset;  
- perpetua.csv : Copiata, la classifica cumulativa dal 92/93 ad oggi;
- largest_win.csv : Tabella creata in excel con risultati trovati online e poi riscritta in file csv;
- h2h_premier.csv : Tabella con statistiche trovate nel sito ufficiale Premier League e scritta in file csv.
Tra i dataset, manualmente, talvolta ho dovuto far combaciare i nomi delle squadre (es. Chelsea FC con FC Chelsea)

''' SPIEGAZIONE DEL CODICE CREA_AVERAGE_AGE ''' 
crea_average_age:
questo programma crea una connessione con il sito di transfermarkt, sapendo che in tale pagina web è presente uan tabella di dati stagionali e ne salva il contenuto, per poi passare, iterando l'url, alla pagine della stagione successiva, finche non ha raccolto tutti i dati richiesti. alla fine, dopo essere stati puliti, i dati vengono collezionati in un unico dataframe, scritto in un nuovo file csv (lo salverà come average_age_copia, non vorrei sovrascrivere il file già comprobato e compromettere il progetto, anche se in caso basterebbe far partire il file elaborazione_df.py cambiando il nome del dataset da caricare a metà script (         df_average = completa_e_ordina(carica_dati("average_age.csv"))   <-- average_age_copia.csv    ).).
P.S. non è necessario eseguire il programma in quanto viene usato il file già conenuto nella cartella (average_age.csv) 

CONTENUTO CARTELLA:
La presente cartella "progetto_calcio" contiene:
- Introduzione.py: file principale da avviare per visualizzare l'intero progetto;
- Pages: cartella contenente le altre pagine del progetto;
- **crea_average_age.py**: dedicato alla raccolta e processing dei dati sull'età media delle squadre;
- **crea_rankings.py**: dedicato alla raccolta e processing delle classifiche intere di tutte le stagioni;
- **elaborazione_df.py**: file usato nel processing dei dataframe, in modo da renderli facilmente lavorabili 
        (aggiunta di "Stagione" ed "Anno" in tutti i dataset, creazione record.csv, formattazione);
- i dataset utilizzati per le analisi (alcuni scraped, altri copiati e altri creati);
- i file generati da uv per gestire le dipendenze;
- l'immagine caricata nella pagine di introduzione.