import os
import json
from fastapi import FastAPI, File, UploadFile, Query
from fastapi.responses import FileResponse, JSONResponse
from core.config.server_config import FINAL_IP, SERVER_URL
from dir_config import AUDIO_DIR, VIDEO_DIR
from lib.tools.video_to_audio_converter import convert_video_to_audio, save_uploaded_file

def register_api_routes(app: FastAPI):

    @app.get("/")
    async def home():
        filepath = os.path.join("web", "pages", "index.html")
        if not os.path.isfile(filepath):
            return JSONResponse({"error": "index.html not found"}, status_code=404)
        return FileResponse(filepath, media_type="text/html")

    async def serve_media_file(directory: str, filename: str):
        try:
            filepath = os.path.join(directory, filename)
            if not os.path.isfile(filepath):
                return JSONResponse({"error": "File not found"}, status_code=404)

            return FileResponse(
                filepath,
                media_type="application/octet-stream",
                filename=filename,
                headers={
                    "Content-Disposition": f'attachment; filename="{filename}"',
                    "Access-Control-Allow-Origin": "*",
                    "Cache-Control": "no-store",
                }
            )

        except Exception as e:
            return JSONResponse({"error": f"Failed to serve file: {str(e)}"}, status_code=500)

    @app.get("/download/audio/{filename:path}")
    async def download_audio(filename: str):
        return await serve_media_file(AUDIO_DIR, filename)

    @app.get("/download/video/{filename:path}")
    async def download_video(filename: str):
        return await serve_media_file(VIDEO_DIR, filename)

    @app.get("/api/check-updates")
    async def check_sonieffect_updates():
        try:
            json_path = os.path.join("core", "config", "updates-data.json")
            if not os.path.isfile(json_path):
                return JSONResponse({"error": "Update data not found"}, status_code=404)

            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Ensure expected keys exist
            build_number = data.get("build_number")
            new_version = data.get("new_version")
            message = data.get("message", "New update available!")

            return {
                "build_number": build_number,
                "new_version": new_version,
                "message": message
            }

        except Exception as e:
            return JSONResponse({"error": f"Failed to read updates: {str(e)}"}, status_code=500)

    @app.post("/api/convert")
    async def convert(
        file: UploadFile = File(...),
        format: str = Query("mp3"),
        bitrate: str = Query("192k")
    ):
        try:
            print(f"[!] INFO: Uploading file: {file.filename}")

            input_path = save_uploaded_file(file)
            print(f"[!] INFO: File saved: {input_path}")

            output_path = convert_video_to_audio(
                input_path,
                out_format=format,
                bitrate=bitrate
            )

            filename = os.path.basename(output_path)
            print(f"[✓] DONE: Conversion completed: {filename}")

            return {
                "status": "success",
                "filename": filename,
                "download_url": f"{SERVER_URL}/download/audio/{filename}"
            }

        except Exception as e:
            print(f"[✕] ERROR: Conversion failed - {str(e)}")
            return JSONResponse({"error": str(e)}, status_code=500)
