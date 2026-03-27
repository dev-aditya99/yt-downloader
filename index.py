import streamlit as st
from pytubefix import YouTube
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.audio.io.AudioFileClip import AudioFileClip
import os

st.set_page_config(
    page_title="YOZO - YouTube Video & Audio Downloader",
    page_icon="🎬",
    layout="centered",
    initial_sidebar_state="auto"
)

st.title("🎥 YOZO - YouTube Downloader")

url = st.text_input("Enter YouTube Video URL")

def progress_func(stream, chunk, bytes_remaining):
    total_size = stream.filesize
    bytes_downloaded = total_size - bytes_remaining
    progress = int((bytes_downloaded / total_size) * 100)
    # Ensure progress bar exists in session state before updating
    if 'download_progress' in st.session_state:
        st.session_state.download_progress.progress(progress / 100)

if url:
    try:
        yt = YouTube(url, on_progress_callback=progress_func)
        st.video(url)
        st.success(f"Title: {yt.title}")

        # Choose between Video or Audio
        download_type = st.radio("Select Download Format", ["Video (High Quality)", "Audio (MP3)"])

        if download_type == "Video (High Quality)":
            # Adaptive video-only streams (higher quality)
            video_streams = yt.streams.filter(adaptive=True, only_video=True, file_extension='mp4').order_by('resolution').desc()
            
            if not video_streams:
                st.error("No suitable video streams found.")
            else:
                quality_options = [stream.resolution for stream in video_streams]
                selected_quality = st.selectbox("Choose high-quality resolution", quality_options)
                selected_video_stream = yt.streams.filter(res=selected_quality, adaptive=True, only_video=True, file_extension='mp4').first()
                
                # Get best audio for the video merge
                audio_stream = yt.streams.filter(adaptive=True, only_audio=True, file_extension='mp4').order_by('abr').desc().first()

                if st.button("Download High-Quality Video"):
                    st.session_state.download_progress = st.progress(0)
                    
                    with st.spinner('Downloading streams...'):
                        # Temporary file names
                        video_path = selected_video_stream.download(filename='temp_video.mp4')
                        audio_path = audio_stream.download(filename='temp_audio.mp4')

                    st.info("🎬 Merging video and audio... This may take a moment.")

                    output_path = "final_output.mp4"
                    
                    # Merge using moviepy
                    # Note: Using try/finally to ensure resources are closed and files deleted
                    try:
                        video_clip = VideoFileClip(video_path)
                        audio_clip = AudioFileClip(audio_path)
                        
                        final_video = video_clip.with_audio(audio_clip)
                        final_video.write_videofile(output_path, codec="libx264", audio_codec="aac", logger=None)
                        
                        # Close clips to release file locks
                        video_clip.close()
                        audio_clip.close()
                        final_video.close()

                        st.success(f"✅ Merging completed!")
                        
                        # Show download button
                        with open(output_path, "rb") as file:
                            st.download_button(
                                label="📥 Download Final Video",
                                data=file,
                                file_name=f"{yt.title}.mp4",
                                mime="video/mp4"
                            )
                    except Exception as e:
                        st.error(f"Error during processing: {e}")
                    finally:
                        # Cleanup temp files
                        if os.path.exists(video_path): os.remove(video_path)
                        if os.path.exists(audio_path): os.remove(audio_path)
                        if os.path.exists(output_path): os.remove(output_path)

        elif download_type == "Audio (MP3)":
            # Audio-only logic
            audio_stream = yt.streams.filter(only_audio=True).order_by('abr').desc().first()
            
            st.info(f"Selected Quality: {audio_stream.abr} (Best Available)")

            if st.button("Download Audio"):
                st.session_state.download_progress = st.progress(0)
                
                with st.spinner('Downloading audio stream...'):
                    # Download original audio (usually m4a or webm)
                    temp_audio_path = audio_stream.download(filename='temp_audio_raw.mp4')
                
                output_audio_path = "final_audio.mp3"
                
                st.info("🎵 Converting to MP3...")
                
                try:
                    # Convert to MP3 using moviepy
                    audio_clip = AudioFileClip(temp_audio_path)
                    audio_clip.write_audiofile(output_audio_path, logger=None)
                    audio_clip.close()

                    st.success(f"✅ Conversion complete!")
                    
                    with open(output_audio_path, "rb") as file:
                        st.download_button(
                            label="📥 Download MP3",
                            data=file,
                            file_name=f"{yt.title}.mp3",
                            mime="audio/mpeg"
                        )
                except Exception as e:
                    st.error(f"Error during conversion: {e}")
                finally:
                    # Cleanup
                    if os.path.exists(temp_audio_path): os.remove(temp_audio_path)
                    if os.path.exists(output_audio_path): os.remove(output_audio_path)

    except Exception as e:
        st.error(f"❌ Error: {e}")