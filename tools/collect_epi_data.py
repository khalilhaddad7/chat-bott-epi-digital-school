"""
Crawler pour le site de l'EPI (episup.com/fr).
Collecte les données du site et les enregistre dans epi_site_data.csv.
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import pandas as pd
import re
import logging
from tqdm import tqdm

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EpiSiteCrawler:
    def __init__(self, base_url="https://episup.com/fr", max_pages=150):
        self.visited = set()
        self.data = []
        self.base_url = base_url
        self.max_pages = max_pages
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        })

    def is_internal_link(self, link):
        parsed = urlparse(link)
        base_parsed = urlparse(self.base_url)
        return parsed.netloc == "" or parsed.netloc == base_parsed.netloc

    def is_valid_content(self, text):
        if not text or len(text) < 40:
            return False
        if re.search(
            r"cliquez ici|en savoir plus|plus d'infos|©|mentions légales|cookie",
            text,
            re.IGNORECASE,
        ):
            return False
        return True

    def clean_text(self, text):
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def extract_page_content(self, url, soup):
        title = soup.title.string.strip() if soup.title else "EPI"

        for heading in soup.find_all(["h1", "h2", "h3"]):
            section_title = self.clean_text(heading.get_text())
            content_parts = []
            next_node = heading.next_sibling

            while next_node:
                if getattr(next_node, "name", None) in ["h1", "h2", "h3"]:
                    break
                if getattr(next_node, "name", None) in ["p", "ul", "ol", "div"]:
                    text = self.clean_text(next_node.get_text())
                    if self.is_valid_content(text):
                        content_parts.append(text)
                next_node = next_node.next_sibling

            if content_parts:
                question = f"{title} - {section_title}"
                anchor = re.sub(r"[^a-z0-9]+", "-", section_title.lower())
                self.data.append([
                    question,
                    "\n".join(content_parts),
                    urlparse(url).path.strip("/").split("/")[0] or "accueil",
                    f"{url}#{anchor}",
                ])

    def crawl(self, url=None):
        if len(self.visited) >= self.max_pages:
            return

        url = url or self.base_url
        if url in self.visited:
            return

        self.visited.add(url)
        logger.info(f"Exploration : {url}")

        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
        except Exception as e:
            logger.warning(f"Erreur accès {url} : {e}")
            return

        soup = BeautifulSoup(response.content, "html.parser")
        self.extract_page_content(url, soup)

        for link in soup.find_all("a", href=True):
            if len(self.visited) >= self.max_pages:
                break
            href = link["href"]
            if href.startswith(("mailto:", "tel:", "javascript:", "#")):
                continue
            absolute_url = urljoin(url, href)
            if self.is_internal_link(absolute_url) and absolute_url not in self.visited:
                self.crawl(absolute_url)

    def save_data(self, filename="epi_site_data.csv"):
        df = pd.DataFrame(
            self.data, columns=["Question", "Réponse", "Catégorie", "URL"]
        )
        df.drop_duplicates(subset=["Réponse"], inplace=True)
        df.to_csv(filename, index=False, encoding="utf-8")
        logger.info(f"Fichier créé avec {len(df)} lignes : {filename}")


if __name__ == "__main__":
    crawler = EpiSiteCrawler(base_url="https://episup.com/fr", max_pages=150)
    crawler.crawl()
    crawler.save_data()
