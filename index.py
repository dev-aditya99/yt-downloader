import streamlit as st
from pytubefix import YouTube
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.audio.io.AudioFileClip import AudioFileClip

import os

st.set_page_config(
    page_title="YOZO - YouTube Video Downloader",
    page_icon="🎬",
    layout="centered",
    initial_sidebar_state="auto"
)

st.title("🎥 YouTube Downloader with High Quality & Progress")

url = st.text_input("Enter YouTube Video URL")

def progress_func(stream, chunk, bytes_remaining):
    total_size = stream.filesize
    bytes_downloaded = total_size - bytes_remaining
    progress = int((bytes_downloaded / total_size) * 100)
    st.session_state.download_progress.progress(progress / 100)

if url:
    try:
        yt = YouTube(url, client='WEB', on_progress_callback=progress_func)
        st.video(url)
        st.success(f"Title: {yt.title}")

        # Adaptive video-only streams (higher quality)
        video_streams = yt.streams.filter(adaptive=True, only_video=True, file_extension='mp4').order_by('resolution').desc()
        quality_options = [stream.resolution for stream in video_streams]
        selected_quality = st.selectbox("Choose high-quality resolution", quality_options)

        selected_video_stream = yt.streams.filter(res=selected_quality, adaptive=True, only_video=True, file_extension='mp4').first()
        audio_stream = yt.streams.filter(adaptive=True, only_audio=True, file_extension='mp4').order_by('abr').desc().first()

        if st.button("Download High-Quality Video"):
            st.session_state.download_progress = st.progress(0)
            
            # Temporary file names
            video_path = selected_video_stream.download(filename='temp_video.mp4')
            audio_path = audio_stream.download(filename='temp_audio.mp4')

            st.info("🎬 Merging video and audio...")

            # Merge using moviepy
            final_video = VideoFileClip(video_path).with_audio(AudioFileClip(audio_path))
            output_path = "final_output.mp4"
            final_video.write_videofile(output_path, codec="libx264", audio_codec="aac")

            st.info(f"✅ 🎬 Merging video and audio completed!")
            
             # Show download button
            with open(output_path, "rb") as file:
              st.download_button(
                 label="📥 Download Final Video",
                 data=file,
                file_name=f"{yt.title}.mp4",
                mime="video/mp4"
                 )
            st.success(f"✅ {yt.title} Download complete!")
            
            # Cleanup temp files
            os.remove(video_path)
            os.remove(audio_path)
            os.remove(output_path)
    except Exception as e:
        st.error(f"❌ Error: {e}")






