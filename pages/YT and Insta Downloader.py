import streamlit as st
from pytubefix import YouTube
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.audio.io.AudioFileClip import AudioFileClip
import yt_dlp
import os
import requests

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="YOZO - YouTube & Instagram Downloader",
    page_icon="🎬",
    layout="centered",
    initial_sidebar_state="auto"
)

st.title("🎥 YOZO - Video, Audio & Image Downloader")
st.markdown("Download high-quality videos, audio, and images from **YouTube** and **Instagram (Reels/Posts)**.")

url = st.text_input("Enter YouTube or Instagram URL")

# --- PROGRESS CALLBACKS ---
def yt_progress_func(stream, chunk, bytes_remaining):
    total_size = stream.filesize
    bytes_downloaded = total_size - bytes_remaining
    progress = int((bytes_downloaded / total_size) * 100)
    if 'download_progress' in st.session_state:
        st.session_state.download_progress.progress(progress / 100)

def ig_progress_hook(d):
    if d['status'] == 'downloading':
        total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
        if total > 0:
            progress = d.get('downloaded_bytes', 0) / total
            if 'download_progress' in st.session_state:
                st.session_state.download_progress.progress(min(progress, 1.0))

# --- MAIN LOGIC ---
if url:
    url_lower = url.lower()
    
    # ==========================================
    #             YOUTUBE LOGIC
    # ==========================================
    if "youtube.com" in url_lower or "youtu.be" in url_lower:
        st.caption("Platform Detected: YouTube 🟥")
        try:
            yt = YouTube(url, on_progress_callback=yt_progress_func)
            st.video(url)
            st.success(f"Title: {yt.title}")

            download_type = st.radio("Select Download Format", ["Video (High Quality)", "Audio (MP3)", "Image (Thumbnail)"])

            # 1. YouTube Video
            if download_type == "Video (High Quality)":
                video_streams = yt.streams.filter(adaptive=True, only_video=True, file_extension='mp4').order_by('resolution').desc()
                
                if not video_streams:
                    st.error("No suitable video streams found.")
                else:
                    quality_options = [stream.resolution for stream in video_streams]
                    selected_quality = st.selectbox("Choose high-quality resolution", quality_options)
                    selected_video_stream = yt.streams.filter(res=selected_quality, adaptive=True, only_video=True, file_extension='mp4').first()
                    audio_stream = yt.streams.filter(adaptive=True, only_audio=True, file_extension='mp4').order_by('abr').desc().first()

                    if st.button("Download High-Quality Video"):
                        st.session_state.download_progress = st.progress(0)
                        
                        with st.spinner('Downloading streams...'):
                            video_path = selected_video_stream.download(filename='temp_video.mp4')
                            audio_path = audio_stream.download(filename='temp_audio.mp4')

                        st.info("🎬 Merging video and audio... This may take a moment.")
                        output_path = "final_output.mp4"
                        
                        try:
                            video_clip = VideoFileClip(video_path)
                            audio_clip = AudioFileClip(audio_path)
                            final_video = video_clip.with_audio(audio_clip)
                            final_video.write_videofile(output_path, codec="libx264", audio_codec="aac", logger=None)
                            
                            video_clip.close()
                            audio_clip.close()
                            final_video.close()

                            st.success(f"✅ Merging completed!")
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
                            if os.path.exists(video_path): os.remove(video_path)
                            if os.path.exists(audio_path): os.remove(audio_path)
                            if os.path.exists(output_path): os.remove(output_path)

            # 2. YouTube Audio
            elif download_type == "Audio (MP3)":
                audio_stream = yt.streams.filter(only_audio=True).order_by('abr').desc().first()
                st.info(f"Selected Quality: {audio_stream.abr} (Best Available)")

                if st.button("Download Audio"):
                    st.session_state.download_progress = st.progress(0)
                    with st.spinner('Downloading audio stream...'):
                        temp_audio_path = audio_stream.download(filename='temp_audio_raw.mp4')
                    
                    output_audio_path = "final_audio.mp3"
                    st.info("🎵 Converting to MP3...")
                    
                    try:
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
                        if os.path.exists(temp_audio_path): os.remove(temp_audio_path)
                        if os.path.exists(output_audio_path): os.remove(output_audio_path)

            # 3. YouTube Thumbnail
            elif download_type == "Image (Thumbnail)":
                if st.button("Fetch Thumbnail"):
                    try:
                        thumb_url = yt.thumbnail_url
                        response = requests.get(thumb_url)
                        if response.status_code == 200:
                            st.image(response.content, caption="YouTube Thumbnail")
                            st.download_button(
                                label="📥 Download Image",
                                data=response.content,
                                file_name=f"{yt.title}_thumbnail.jpg",
                                mime="image/jpeg"
                            )
                        else:
                            st.error("Could not fetch the thumbnail.")
                    except Exception as e:
                        st.error(f"Error: {e}")

        except Exception as e:
            st.error(f"❌ YouTube Error: {e}")

   # ==========================================
    #            INSTAGRAM LOGIC
    # ==========================================
    elif "instagram.com" in url_lower:
        st.caption("Platform Detected: Instagram 🟪")
        try:
            ydl_opts_info = {
                'quiet': True, 
                'no_warnings': True
            }
            with yt_dlp.YoutubeDL(ydl_opts_info) as ydl:
                with st.spinner("Fetching Instagram media info..."):
                    info_dict = ydl.extract_info(url, download=False)
            
            if not info_dict:
                st.warning("⚠️ Metadata nahi mil paya. Ye private post ho sakti hai.")
            else:
                video_title = info_dict.get('title', info_dict.get('id', 'Instagram_Media'))
                st.success("✅ Instagram Media Found!")
                
                download_type = st.radio("Select Download Format", ["Video", "Audio (MP3)", "Image(s)"])
                
                # --- Video Download ---
                if download_type == "Video":
                    if st.button("Download Instagram Video"):
                        st.session_state.download_progress = st.progress(0)
                        temp_ig_video = "temp_ig_video.mp4"
                        
                        ydl_opts = {
                            'format': 'best',
                            'outtmpl': temp_ig_video,
                            'quiet': True,
                            'progress_hooks': [ig_progress_hook]
                        }
                        
                        with st.spinner('Downloading Instagram Video...'):
                            try:
                                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                                    ydl.download([url])
                                
                                st.success("✅ Download completed!")
                                with open(temp_ig_video, "rb") as file:
                                    st.download_button(
                                        label="📥 Download Video",
                                        data=file,
                                        file_name=f"{video_title}.mp4",
                                        mime="video/mp4"
                                    )
                            except Exception as e:
                                st.error(f"Error downloading: {e}")
                            finally:
                                if os.path.exists(temp_ig_video): os.remove(temp_ig_video)

                # --- Audio Download ---
                elif download_type == "Audio (MP3)":
                    if st.button("Download Instagram Audio"):
                        st.session_state.download_progress = st.progress(0)
                        temp_ig_video = "temp_ig_audio_raw.mp4"
                        output_ig_audio = "final_ig_audio.mp3"
                        
                        ydl_opts = {
                            'format': 'best', 
                            'outtmpl': temp_ig_video,
                            'quiet': True,
                            'progress_hooks': [ig_progress_hook]
                        }
                        
                        with st.spinner('Downloading media from Instagram...'):
                            try:
                                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                                    ydl.download([url])
                                    
                                st.info("🎵 Converting to MP3...")
                                audio_clip = AudioFileClip(temp_ig_video)
                                audio_clip.write_audiofile(output_ig_audio, logger=None)
                                audio_clip.close()

                                st.success("✅ Conversion complete!")
                                with open(output_ig_audio, "rb") as file:
                                    st.download_button(
                                        label="📥 Download MP3",
                                        data=file,
                                        file_name=f"{video_title}.mp3",
                                        mime="audio/mpeg"
                                    )
                            except Exception as e:
                                st.error(f"Error during conversion: {e}")
                            finally:
                                if os.path.exists(temp_ig_video): os.remove(temp_ig_video)
                                if os.path.exists(output_ig_audio): os.remove(output_ig_audio)

                # --- Image(s) Fetch ---
                elif download_type == "Image(s)":
                    if st.button("Fetch Image(s)"):
                        try:
                            entries = info_dict.get('entries', [info_dict])
                            images_found = False

                            for idx, entry in enumerate(entries):
                                img_url = entry.get('thumbnail')
                                if img_url:
                                    images_found = True
                                    response = requests.get(img_url)
                                    if response.status_code == 200:
                                        st.image(response.content, caption=f"Image {idx+1}")
                                        st.download_button(
                                            label=f"📥 Download Image {idx+1}",
                                            data=response.content,
                                            file_name=f"IG_Image_{idx+1}.jpg",
                                            mime="image/jpeg",
                                            key=f"ig_img_{idx}" 
                                        )
                                        st.markdown("---")
                                        
                            if not images_found:
                                st.error("No extractable images found in this link.")
                                
                        except Exception as e:
                            st.error(f"Error fetching Instagram image: {e}")

        # === THE MAIN ERROR CATCH ===
        except Exception as e:
            error_msg = str(e)
            # Check for the specific 'no video' text inside the error string
            if "There is no video in this post" in error_msg:
                st.warning("📸 **Image Post Detected:** Ye link sirf photos/carousels ka hai. `yt-dlp` bina Instagram login (Cookies) ke image-only posts ko fetch nahi kar pata kyonki Instagram ise block kar deta hai.")
                st.info("💡 **Tip:** Agar aapko Instagram images reliably download karni hain, toh aapko 'instaloader' library use karni padegi ya yt-dlp me browser cookies pass karni hongi.")
            else:
                st.error("❌ Instagram Error: Ye post private ho sakti hai ya link invalid hai. \n\n *(Note: Private accounts cannot be downloaded without cookies)*")
    else:
        st.warning("⚠️ Please enter a valid YouTube or Instagram URL.")