import yt_dlp
from flask import Flask, request, jsonify, send_file
import os

app = Flask(__name__)

# Use a raw string to avoid the Unicode escape error
DOWNLOAD_FOLDER = r"C:\Users\user\Downloads"

# Ensure the download folder exists
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

@app.route("/download", methods=["GET"])
def download_video():
    video_url = request.args.get("url")
    if not video_url:
        return jsonify({"error": "Please provide a YouTube video URL."}), 400

    try:
        # Use yt-dlp to download the video
        ydl_opts = {
            'outtmpl': os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s'),
            'keep_video': True,  # This option prevents the temporary files from being deleted
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(video_url, download=True)
            filename = ydl.prepare_filename(info_dict)

        return send_file(filename, as_attachment=True, download_name=f"{info_dict['title']}.mp4")
    
    except Exception as e:
        return jsonify({"error": "Failed to download the video.", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
