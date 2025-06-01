
import os
import uuid
from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from starlette.background import BackgroundTask
from starlette.responses import FileResponse
import shutil
import time

app = FastAPI()
uploads = {}
TMP_DIR = "/tmp"

@app.post("/upload")
async def upload(file: UploadFile):
    if not file.filename.endswith(".ipa"):
        raise HTTPException(status_code=400, detail="Nur .ipa-Dateien erlaubt.")

    file_id = str(uuid.uuid4())
    file_path = os.path.join(TMP_DIR, f"{file_id}.ipa")

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    expire_time = time.time() + 600  # 10 Minuten
    uploads[file_id] = {"path": file_path, "expires": expire_time}

    return JSONResponse(content={"link": f"/stream/{file_id}"})

@app.get("/stream/{file_id}")
async def stream(file_id: str):
    info = uploads.get(file_id)
    if not info or time.time() > info["expires"]:
        raise HTTPException(status_code=404, detail="Link abgelaufen oder ungültig.")

    def cleanup():
        if os.path.exists(info["path"]):
            os.remove(info["path"])
        uploads.pop(file_id, None)

    return FileResponse(info["path"], background=BackgroundTask(cleanup), media_type='application/octet-stream', filename=f"{file_id}.ipa")
