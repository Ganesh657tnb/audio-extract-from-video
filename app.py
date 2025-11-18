import os
import streamlit as st
import tempfile
import subprocess
from io import BytesIO

# --- Configuration & Setup ---
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'webm', 'mkv'}

# --- FFmpeg Utilities ---

def extract_audio_ffmpeg(video_path, output_wav_path):
    """
    Extracts the audio stream from a video file into an uncompressed WAV format (pcm_s16le).
    This format is ideal as an intermediate step.
    """
    try:
        # -y: overwrite output file without asking; -vn: no video; -acodec pcm_s16le: raw, uncompressed WAV
        subprocess.run([
            "ffmpeg", "-y", "-i", video_path,
            "-vn", "-acodec", "pcm_s16le",
            output_wav_path
        ], check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        st.error(f"FFmpeg extraction failed! Output: {e.stderr.decode()}")
        raise
    except FileNotFoundError:
        st.error("FFmpeg not found. Please ensure it is installed and in your system PATH.")
        raise

def convert_to_mp3_ffmpeg(input_wav_path, output_mp3_path):
    """Converts the extracted WAV to a portable MP3 format."""
    try:
        # -acodec libmp3lame: use the standard MP3 encoder
        # -q:a 2: VBR quality preset (V0) - high quality, reasonable size
        subprocess.run([
            "ffmpeg", "-y", "-i", input_wav_path,
            "-acodec", "libmp3lame",
            "-q:a", "2",
            output_mp3_path
        ], check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        st.error(f"FFmpeg MP3 conversion failed! Output: {e.stderr.decode()}")
        raise
        
# --- Core Processing Logic ---

@st.cache_data
def extract_audio_for_download(video_bytes, original_filename, output_format="mp3"):
    """
    Handles file saving, FFmpeg execution, and returns the final audio bytes.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        # Define temporary file paths
        temp_video_path = os.path.join(temp_dir, original_filename)
        temp_audio_wav = os.path.join(temp_dir, "temp_audio.wav")
        final_audio_path = os.path.join(temp_dir, f"extracted_audio.{output_format}")

        # 1. Save uploaded video bytes
        with open(temp_video_path, "wb") as f:
            f.write(video_bytes)
        
        try:
            # 2. Extract raw WAV audio
            extract_audio_ffmpeg(temp_video_path, temp_audio_wav)

            if output_format == "mp3":
                # 3. Convert WAV to MP3
                convert_to_mp3_ffmpeg(temp_audio_wav, final_audio_path)
            else:
                # If WAV is requested, just use the extracted WAV
                final_audio_path = temp_audio_wav
                
            # 4. Read the final audio bytes
            with open(final_audio_path, "rb") as f:
                audio_bytes = f.read()
            
            return audio_bytes
            
        except Exception:
            # Errors are already logged within the utility functions
            return None

# --- Streamlit App Function ---

def main():
    st.title("✂️ Video Audio Extractor")
    st.markdown("Upload any video file to download its separate audio track in MP3 or WAV format.")
    
    st.info("FFmpeg is required for this app to work.")

    uploaded_file = st.file_uploader("Choose a Video File", type=list(ALLOWED_EXTENSIONS))
    
    if uploaded_file:
        video_bytes = uploaded_file.read()
        
        # Display the video for context
        st.subheader("Video Preview")
        st.video(video_bytes)
        
        # User selects the output format
        output_format = st.radio("Select Output Audio Format:", ["mp3", "wav"])
        
        if st.button("Extract and Prepare for Download"):
            
            with st.spinner(f"Processing... Extracting audio and converting to {output_format.upper()}..."):
                # Call the cached processing function
                audio_data = extract_audio_for_download(video_bytes, uploaded_file.name, output_format)
            
            if audio_data:
                # Provide the download button
                base_name = uploaded_file.name.rsplit('.', 1)[0]
                mime_type = f"audio/{output_format}" if output_format == 'mp3' else "audio/wav"
                
                st.subheader("✅ Download Ready")
                st.download_button(
                    label=f"Download {base_name}_extracted.{output_format}",
                    data=audio_data,
                    file_name=f"{base_name}_extracted.{output_format}",
                    mime=mime_type
                )
            else:
                st.error("Extraction failed. Check the error logs above.")

if __name__ == "__main__":
    main()