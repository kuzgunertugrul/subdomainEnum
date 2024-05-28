import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import sys
import warnings

# Suppress only the InsecureRequestWarning from urllib3
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

def is_valid(url):
    parsed = urlparse(url)
    return bool(parsed.netloc) and bool(parsed.scheme)

def get_all_website_links(url, domain_name):
    urls = set()
    try:
        response = requests.get(url, verify=False)
        soup = BeautifulSoup(response.content, "html.parser")
        for a_tag in soup.findAll("a"):
            href = a_tag.attrs.get("href")
            if href == "" or href is None:
                continue
            href = urljoin(url, href)
            href_parsed = urlparse(href)
            href = href_parsed.scheme + "://" + href_parsed.netloc + href_parsed.path
            if not is_valid(href):
                continue
            if domain_name not in href:
                continue
            urls.add(href)
    except requests.exceptions.RequestException as e:
        print(f"Error crawling {url}: {e}")
    return urls

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 crawler.py <subdomain>")
        sys.exit(1)

    subdomain = sys.argv[1]
    domain_name = urlparse(subdomain).netloc
    crawled_urls = get_all_website_links(subdomain, domain_name)
    
    with open(f"subdomain_results/crawled_urls_{subdomain.replace('://', '_')}.txt", "w") as f:
        for url in crawled_urls:
            f.write(url + "\n")
    print(f"[*] Crawling {subdomain} completed. Found {len(crawled_urls)} URLs.")