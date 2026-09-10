from app.core.database import get_meili_client

def index_note(note_id: str, extracted_text: str, filename: str, extension: str):
    """Aggiunge o aggiorna il documento nell'indice 'notes'."""
    client = get_meili_client()
    document = {
        "id": note_id,
        "filename": filename,
        "extension": extension,
        "extracted_text": extracted_text
    }
    
    try:
        # MeiliSearch utilizza 'id' come primary key per l'inserimento
        client.index('notes').add_documents([document])
    except Exception as e:
        print(f"Errore durante l'indicizzazione in MeiliSearch per {note_id}: {e}")

def query_notes(query_string: str, limit: int = 20):
    """Esegue una fuzzy search restituendo gli ID e frammenti di testo evidenziati."""
    client = get_meili_client()
    
    try:
        # attributesToHighlight farà in modo che MeiliSearch restituisca il testo 
        # con tag <em> attorno alle parole trovate, utile per il frontend
        results = client.index('notes').search(query_string, {
            'limit': limit,
            'attributesToHighlight': ['extracted_text']
        })
        return results.get('hits', [])
    except Exception as e:
        print(f"Errore durante la ricerca: {e}")
        return []