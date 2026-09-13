import io
import re
import zipfile

from app.core.database import get_notes_by_ids


def _sanitize_archive_name(name: str) -> str:
    """Rende un titolo/filename sicuro da usare come nome file dentro lo zip."""
    name = re.sub(r'[\\/*?:"<>|]', "_", (name or "").strip())
    return name[:80] or "nota"


def _unique_archive_name(raw_name: str, used_names: set) -> str:
    """Evita che due note con lo stesso titolo si sovrascrivano nello zip."""
    base = _sanitize_archive_name(raw_name)
    candidate = f"{base}.txt"
    counter = 2
    while candidate in used_names:
        candidate = f"{base} ({counter}).txt"
        counter += 1
    used_names.add(candidate)
    return candidate


def build_transcripts_zip(note_ids: list[str]) -> tuple[io.BytesIO, int]:
    """Costruisce in memoria uno .zip con un file .txt per ogni nota trovata
    tra `note_ids` (una trascrizione per file, nominata dal titolo automatico
    o dal filename originale).

    Usata dall'endpoint POST /api/notes/export, richiamato sia dal pulsante
    "Esporta .zip" della web app sia dal bottone equivalente sul bot Telegram,
    entrambi passano gli id delle note ottenute da una ricerca.

    Ritorna il buffer già posizionato all'inizio (pronto per essere letto) e
    il numero di note effettivamente incluse: gli id inesistenti (es. nota
    cancellata nel frattempo) vengono ignorati silenziosamente invece di far
    fallire l'intera esportazione.
    """
    notes = get_notes_by_ids(note_ids)

    buffer = io.BytesIO()
    used_names = set()

    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for note in notes:
            text = note["extracted_text"] or "[Nessun testo estratto disponibile per questo file]"
            archive_name = _unique_archive_name(note["title"] or note["filename"], used_names)
            zf.writestr(archive_name, text)

    buffer.seek(0)
    return buffer, len(notes)