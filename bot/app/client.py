import httpx

from app.core.config import BACKEND_URL


class BackendError(Exception):
    """Sollevata quando il backend TELA risponde con un errore."""


async def upload_file(filename: str, content: bytes, mime_type: str | None) -> dict:
    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(
            f"{BACKEND_URL}/api/upload",
            files={"file": (filename, content, mime_type or "application/octet-stream")},
        )
    if resp.status_code != 200:
        raise BackendError(f"Upload fallito ({resp.status_code}): {resp.text}")
    return resp.json()


async def search_notes(query: str) -> dict:
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(f"{BACKEND_URL}/api/search", params={"q": query})
    if resp.status_code != 200:
        raise BackendError(f"Ricerca fallita ({resp.status_code}): {resp.text}")
    return resp.json()


async def get_note_details(note_id: str) -> dict:
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(f"{BACKEND_URL}/api/notes/{note_id}")
    if resp.status_code != 200:
        raise BackendError(f"Nota non trovata ({resp.status_code}): {resp.text}")
    return resp.json()


async def download_note_file(note_id: str) -> tuple[bytes, str]:
    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.get(f"{BACKEND_URL}/api/notes/{note_id}/file")
    if resp.status_code != 200:
        raise BackendError(f"Download fallito ({resp.status_code}): {resp.text}")

    filename = None
    content_disposition = resp.headers.get("content-disposition", "")
    if "filename=" in content_disposition:
        filename = content_disposition.split("filename=")[-1].strip('"; ')

    if not filename:
        details = await get_note_details(note_id)
        filename = details.get("filename", note_id)

    return resp.content, filename
