import streamlit as st
import requests
from PIL import Image
from io import BytesIO
from ddgs import DDGS

import instaloader
import re

st.set_page_config(
    page_title="ImageX - Search & Download",
    page_icon="🌌",
    layout="centered"
)

# --- SESSION STATE INITIALIZATION ---
# Page refresh hone par in variables me data save rahega
if 'search_results' not in st.session_state:
    st.session_state.search_results = []
if 'generic_image' not in st.session_state:
    st.session_state.generic_image = None
if 'ig_images' not in st.session_state:
    st.session_state.ig_images = []

st.title("🌌 ImageX - Universal Image Hub")
st.markdown("Search across the web, download from any direct link, or fetch Instagram posts seamlessly.")

tab_search, tab_url, tab_ig = st.tabs(["🔍 Search Images", "🌐 Generic URL", "🟪 Instagram Post"])

# ==========================================
#         TAB 1: IMAGE SEARCH ENGINE
# ==========================================
with tab_search:
    st.subheader("Search & Download Images")
    search_query = st.text_input("What do you want to search?", value="Lord Hari in cosmic setting")
    num_results = st.slider("Number of images to fetch", min_value=3, max_value=15, value=6, step=3)
    
    if st.button("Search Images"):
        with st.spinner("Searching the web..."):
            try:
                results = DDGS().images(search_query, max_results=num_results)
                if results:
                    # Naya search hone par purana state clear karke naya data daalein
                    st.session_state.search_results = []
                    for idx, res in enumerate(results):
                        img_url = res.get('image')
                        try:
                            img_response = requests.get(img_url, timeout=5)
                            if img_response.status_code == 200:
                                st.session_state.search_results.append({
                                    "content": img_response.content,
                                    "url": img_url,
                                    "id": idx
                                })
                        except:
                            pass # Agar koi ek image fail ho jaye toh aage badho
                else:
                    st.warning("No results found. Try different keywords.")
            except Exception as e:
                st.error(f"Search Error: {e}")

    # Display logic button ke bahar rakha hai
    if st.session_state.search_results:
        cols = st.columns(3)
        for idx, item in enumerate(st.session_state.search_results):
            with cols[idx % 3]:
                st.image(item["content"], use_container_width=True)
                st.download_button(
                    label="📥 Download",
                    data=item["content"],
                    file_name=f"Search_{item['id']+1}.jpg",
                    mime="image/jpeg",
                    key=f"search_dl_{item['id']}" # Unique key is compulsory
                )

# ==========================================
#         TAB 2: GENERIC URL DOWNLOADER
# ==========================================
with tab_url:
    st.subheader("Download from Any Image Link")
    direct_url = st.text_input("Enter Direct Image URL")
    
    if st.button("Fetch Image"):
        if direct_url:
            with st.spinner("Fetching your image..."):
                try:
                    response = requests.get(direct_url, timeout=10)
                    if response.status_code == 200:
                        st.session_state.generic_image = response.content
                    else:
                        st.error("Could not fetch the image.")
                except Exception as e:
                    st.error(f"Error fetching URL: {e}")
        else:
            st.warning("Please enter a URL first.")

    if st.session_state.generic_image:
        img = Image.open(BytesIO(st.session_state.generic_image))
        st.image(img, caption="Fetched Image", use_container_width=True)
        st.download_button(
            label="📥 Download Image",
            data=st.session_state.generic_image,
            file_name="generic_download.jpg",
            mime="image/jpeg",
            key="dl_generic"
        )

# ==========================================
#         TAB 3: INSTAGRAM POST DOWNLOADER
# ==========================================
with tab_ig:
    st.subheader("Instagram Post Downloader")
    ig_url = st.text_input("Enter Instagram Post URL (e.g., https://www.instagram.com/p/...)")
    
    if st.button("Extract Instagram Images"):
        if ig_url:
            with st.spinner("Bypassing IG and fetching media..."):
                try:
                    match = re.search(r'/(?:p|reel)/([^/?#&]+)', ig_url)
                    if match:
                        shortcode = match.group(1)
                        L = instaloader.Instaloader()
                        post = instaloader.Post.from_shortcode(L.context, shortcode)
                        
                        st.session_state.ig_images = [] # Clear previous IG images
                        st.success("✅ Post Found!")
                        
                        if post.typename == 'GraphSidecar':
                            st.info("This is a Carousel post with multiple images.")
                            for idx, node in enumerate(post.get_sidecar_nodes()):
                                if node.is_video:
                                    st.warning(f"Slide {idx+1} is a video. Skipped.")
                                else:
                                    resp = requests.get(node.display_url)
                                    st.session_state.ig_images.append({
                                        "content": resp.content,
                                        "caption": f"Slide {idx+1}",
                                        "filename": f"IG_{shortcode}_{idx+1}.jpg",
                                        "id": idx
                                    })
                        else:
                            if post.is_video:
                                st.warning("This is a Video post. Please use the YOZO app for videos.")
                            else:
                                resp = requests.get(post.url)
                                st.session_state.ig_images.append({
                                    "content": resp.content,
                                    "caption": "Instagram Image",
                                    "filename": f"IG_{shortcode}.jpg",
                                    "id": 0
                                })
                    else:
                        st.error("Invalid Instagram URL format. Kripya URL check karein.")
                except Exception as e:
                    st.error(f"Error: {e}. \n\n*Note: Private accounts or rate-limits might cause this.*")
        else:
            st.warning("Please enter an Instagram URL.")

    # Display logic for Instagram Images
    if st.session_state.ig_images:
        for item in st.session_state.ig_images:
            st.image(item["content"], caption=item["caption"])
            st.download_button(
                label=f"📥 Download {item['caption']}",
                data=item["content"],
                file_name=item["filename"],
                mime="image/jpeg",
                key=f"dl_ig_{item['id']}" # Crucial unique key
            )
            st.markdown("---")