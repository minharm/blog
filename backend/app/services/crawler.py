import re
import httpx
from bs4 import BeautifulSoup

class NaverCrawler:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    def parse_url(self, url: str):
        path_match = re.search(r"blog\.naver\.com/([a-zA-Z0-9_-]+)/(\d+)", url)
        if path_match:
            return path_match.group(1), path_match.group(2)

        blog_id_match = re.search(r"blogId=([a-zA-Z0-9_-]+)", url)
        log_no_match = re.search(r"logNo=(\d+)", url)
        if blog_id_match and log_no_match:
            return blog_id_match.group(1), log_no_match.group(2)

        raise ValueError("지원하지 않거나 올바르지 않은 네이버 블로그 주소 형식입니다.")

    async def extract_text(self, url: str):
        blog_id, log_no = self.parse_url(url)
        target_url = f"https://blog.naver.com/PostView.naver?blogId={blog_id}&logNo={log_no}"

        async with httpx.AsyncClient() as client:
            response = await client.get(target_url, headers=self.headers)
            if response.status_code != 200:
                raise Exception("네이버 블로그 데이터를 가져오는 데 실패했습니다.")

        soup = BeautifulSoup(response.text, "html.parser")

        title_node = soup.select_one(".se-title-text") or soup.select_one(".pcol1")
        title = title_node.get_text().strip() if title_node else "제목 없음"

        content_node = (
            soup.select_one(".se-main-container") or 
            soup.select_one(".se-viewer") or 
            soup.find("div", id=re.compile(r"^post-view"))
        )

        if not content_node:
            content_node = soup.body

        images = []
        img_tags = content_node.find_all("img")
        for img in img_tags:
            # 🎯 data-source 속성에 이미 고화질 원본 주소가 온전하게 들어있습니다.
            # 어떤 강제 변형도 가하지 않고 이 원본 주소를 그대로 가져오는 것이 가장 안전하고 선명합니다.
            img_url = img.get("data-source") or img.get("data-lazy-src") or img.get("data-src") or img.get("src")
            
            if img_url:
                if "static.naver.net" in img_url or "bg_" in img_url or "sticker" in img_url:
                    continue
                
                # 중복을 제거하고 유효한 프로토콜 주소만 정렬하여 매핑
                if img_url not in images and img_url.startswith("http"):
                    images.append(img_url)

        clean_text = re.sub(r'\n+', '\n', content_node.get_text()).strip()
        return clean_text, title, images