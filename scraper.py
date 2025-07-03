import requests
from bs4 import BeautifulSoup

def get_current_price(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        price = soup.find("span", class_="pdp-price").text.strip()
        return float(price.replace('₹', '').replace(',', ''))
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None