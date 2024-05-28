#!/bin/bash

# Required tools: subfinder, amass, assetfinder, httprobe, python3, pip, aquatone

# Check if all required tools are installed
for tool in subfinder amass assetfinder httprobe python3 aquatone; do
    if ! command -v $tool &> /dev/null; then
        echo "$tool is not installed. Please install it to use this script."
        exit 1
    fi
done

# Check if requests, beautifulsoup4, tqdm and validators are installed for Python
if ! python3 -c "import requests; import bs4; import tqdm; import validators" &> /dev/null; then
    echo "Python packages requests, beautifulsoup4, tqdm, and validators are not installed. Installing..."
    pip install requests beautifulsoup4 tqdm validators
fi

# Check if domain is provided
if [ -z "$1" ]; then
    echo "Usage: $0 <domain>"
    exit 1
fi

DOMAIN=$1

# Create a directory to store results
mkdir -p subdomain_results

# Check if there are previous results and ask to resume or clean up
if [ -f subdomain_results/valid_subdomains.txt ]; then
    read -p "[*] Previous session found. Do you want to resume the previous session? (y/n): " resume
    if [ "$resume" != "y" ]; then
        echo "[*] Cleaning up previous session..."
        rm -rf subdomain_results
        mkdir -p subdomain_results
    else
        echo "[*] Resuming previous session..."
    fi
fi

# Run subfinder
echo "[*] Running subfinder..."
subfinder -d $DOMAIN -silent > subdomain_results/subfinder.txt

# Run amass
echo "[*] Running amass..."
amass enum -passive -d $DOMAIN -o subdomain_results/amass_raw.txt

# Clean up amass output
grep -Eo "([a-zA-Z0-9-]+\.)*$DOMAIN" subdomain_results/amass_raw.txt > subdomain_results/amass.txt

# Run assetfinder
echo "[*] Running assetfinder..."
assetfinder --subs-only $DOMAIN > subdomain_results/assetfinder.txt

# Combine results into one file and remove duplicates
rm subdomain_results/amass_raw.txt
cat subdomain_results/*.txt | sort -u > subdomain_results/all_subdomains.txt

# Check which subdomains are valid and reachable
echo "[*] Validating subdomains with httprobe..."
cat subdomain_results/all_subdomains.txt | httprobe > subdomain_results/valid_subdomains_raw.txt

# Filter out http URLs if https URLs exist
awk -F/ '!seen[$3]++ || $1 == "https:"' subdomain_results/valid_subdomains_raw.txt > subdomain_results/valid_subdomains.txt

TOTAL_SUBDOMAINS=$(wc -l < subdomain_results/valid_subdomains.txt)
echo "[*] Total valid subdomains: $TOTAL_SUBDOMAINS"

# Ask if user wants to start crawling
read -p "[*] Do you want to start crawling the subdomains? (y/n): " start_crawl
if [ "$start_crawl" == "y" ]; then
    echo "[*] Starting crawling..."
    while read -r subdomain; do
        echo "[*] Crawling $subdomain"
        python3 crawler.py "$subdomain"
    done < subdomain_results/valid_subdomains.txt
    echo "[*] Crawling completed."
fi

# Combine all found URLs from crawling into one file
cat subdomain_results/crawled_urls_*.txt | sort -u > subdomain_results/all_crawled_urls.txt

# Ask if user wants to start Aquatone for screenshots
read -p "[*] Do you want to take screenshots of the URLs with Aquatone? (y/n): " start_aquatone
if [ "$start_aquatone" == "y" ]; then
    echo "[*] Taking screenshots with Aquatone..."
    cat subdomain_results/all_crawled_urls.txt | aquatone -out aquatone_report
    echo "[*] Screenshots taken. Check the 'aquatone_report' directory."
fi

# Ask if user wants to start vulnerability testing
read -p "[*] Do you want to start vulnerability testing? (y/n): " start_vuln_test
if [ "$start_vuln_test" == "y" ]; then
    echo "[*] Testing vulnerabilities on found URLs..."
    COUNT=0
    TOTAL_URLS=$(wc -l < subdomain_results/all_crawled_urls.txt)
    while read -r url; do
        COUNT=$((COUNT + 1))
        echo "[*] Testing $url ($COUNT/$TOTAL_URLS)"
        python3 test_vulnerabilities.py "$url"
    done < subdomain_results/all_crawled_urls.txt
fi

# Clean up temporary files (optional, uncomment if needed)
# rm -rf subdomain_results