from dotenv import load_dotenv
from tavily import TavilyClient
from bs4 import BeautifulSoup
import requests
import os
from langchain_community.chat_models import ChatOllama
from langchain_ollama import ChatOllama

load_dotenv()

llm = ChatOllama(model="llama3", temperature=0)

tavily_api_key = os.getenv("TAVILY_API_KEY")
client = TavilyClient(api_key=tavily_api_key)

def extract_relevant_images(page_url, max_images=3):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(page_url, headers=headers, timeout=5)
        soup = BeautifulSoup(response.text, "html.parser")
        images = []
        for img in soup.find_all("img"):
            src = img.get("src", "")
            alt = img.get("alt", "").lower()
            if not src or src.startswith("data:"):
                continue
            if any(kw in alt for kw in ["logo", "icon", "header"]):
                continue
            if src.startswith("//"):
                src = "https:" + src
            elif src.startswith("/"):
                from urllib.parse import urljoin
                src = urljoin(page_url, src)
            images.append((src, alt))
            if len(images) >= max_images:
                break
        return images
    except Exception as e:
        print(f"Image scrape failed from {page_url}: {e}")
        return []
    
def fetch_youtube_links(query: str, max_results: int = 5):
    """Performs a dedicated YouTube-only search using Tavily."""
    yt_query = f"{query} site:youtube.com"
    try:
        yt_response = client.search(query=yt_query, max_results=max_results, search_depth="advanced")
        links = []
        for result in yt_response["results"]:
            title = result["title"]
            url = result["url"]
            if "youtube" in url:
                links.append(f"- [{title}]({url})")
        return links
    except Exception as e:
        print(f"❌ Failed to fetch YouTube links: {e}")
        return []


def web_search_tool(query: str):
    """
    Performs a grouped search with:
    - YouTube links (guaranteed via secondary search if needed)
    - Article blocks (text + images from the same article)
    """
    time_filtered_query = f"{query} after:2022-01-01 before:2022-07-01"
    response = client.search(query=time_filtered_query, search_depth="advanced", max_results=10)

    youtube_links = []
    article_blocks = []

    for x in response["results"]:
        title = x["title"]
        content = x["content"]
        url = x["url"]

        if "youtube.com" in url or "youtu.be" in url:
            youtube_links.append(f"- [{title}]({url})")
            continue

        image_tags = []
        for img_url, alt_text in extract_relevant_images(url):
            image_tags.append(f"![{alt_text or 'Image'}]({img_url})")

        article_block = f"""
### {title}

{content}

{'\n'.join(image_tags) if image_tags else ''}

🔗 [Visit Source]({url})
"""
        article_blocks.append(article_block.strip())

    # Ensure YouTube links are present — fallback if missing
    if not youtube_links:
        print("⚠️ No YouTube links found in main results — running fallback search...")
        youtube_links = fetch_youtube_links(query)

    # Final output assembly
    final_output = []

    if youtube_links:
        final_output.append("## 📺 YouTube Links\n" + "\n".join(youtube_links))
    else:
        final_output.append("## 📺 YouTube Links\n_No YouTube videos found._")

    if article_blocks:
        final_output.append("## 📰 Article Summaries with Images\n" + "\n\n---\n\n".join(article_blocks))

    return "\n\n".join(final_output)

    

