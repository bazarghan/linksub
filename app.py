import os
import requests
from flask import Flask, render_template, request, session, redirect, url_for
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import logging

load_dotenv()

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "fallback_dev_key_if_missing")
PROXY_PASSWORD = os.getenv("PROXY_PASSWORD", "123456")

TARGET_SERVER_URL = os.getenv("TARGET_SERVER_URL", "http://localhost:8080")

@app.route('/login/<path:subpath>', methods=['GET', 'POST'])
def login(subpath):
    error = None
    if request.method == 'POST':
        if request.form.get('password') == PROXY_PASSWORD:
            session['authenticated'] = True
            return redirect(f"/{subpath}")
        else:
            error = "رمز عبور اشتباه است."
    return render_template('login.html', subpath=subpath, error=error)

@app.route('/<path:subpath>')
def proxy_subscription(subpath):
    if not session.get('authenticated'):
        return redirect(url_for('login', subpath=subpath))
        
    base_url = TARGET_SERVER_URL.rstrip('/')
    target_url = f"{base_url}/{subpath}"
    
    app.logger.info(f"Received request for path: /{subpath}")
    app.logger.info(f"Forwarding to target URL: {target_url}")
    
    try:
        # Fetch original HTML with browser-like headers to ensure we get the HTML page
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9"
        }
        response = requests.get(target_url, headers=headers, timeout=10)
        app.logger.info(f"Target responded with status code: {response.status_code}")
        app.logger.info(f"Response text snippet (first 1000 chars):\n{response.text[:1000]}")
        
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Define default data structure
        data = {
            "download": "نامشخص",
            "upload": "نامشخص",
            "used": "نامشخص",
            "total": "نامشخص",
            "remained": "نامشخص",
            "expire": "نامشخص",
            "lastonline": "نامشخص",
            "status": "نامشخص"
        }
        
        # Extract data from <template id="subscription-data">
        template_tag = soup.find('template', id='subscription-data')
        
        if template_tag:
            attrs = template_tag.attrs
            data["download"] = attrs.get('data-download', data["download"])
            data["upload"] = attrs.get('data-upload', data["upload"])
            data["used"] = attrs.get('data-used', data["used"])
            data["total"] = attrs.get('data-total', data["total"])
            data["remained"] = attrs.get('data-remained', data["remained"])
            data["expire"] = attrs.get('data-expire', data["expire"])
            data["lastonline"] = attrs.get('data-lastonline', data["lastonline"])
            data["status"] = attrs.get('data-status', data["status"])
            
        # Force status to Active as requested
        data["status"] = "Active"
                    
        # Fallback for expire: look for th containing "Expiry" or "انقضا"
        if data["expire"] in ["نامشخص", "0", "", "None", None] or not data["expire"]:
            expire_th = soup.find(lambda tag: tag.name == "th" and tag.get_text() and ("Expiry" in tag.get_text() or "انقضا" in tag.get_text() or "expiry" in tag.get_text().lower()))
            if expire_th:
                expire_td = expire_th.find_next_sibling('td')
                if expire_td:
                    data["expire"] = expire_td.get_text(strip=True)

        # Fallback for lastonline: look for th containing "Last Online" or "آخرین"
        if data["lastonline"] in ["نامشخص", "", "None", None] or not data["lastonline"] or str(data["lastonline"]).isdigit():
            lastonline_th = soup.find(lambda tag: tag.name == "th" and tag.get_text() and ("Last Online" in tag.get_text() or "آنلاین" in tag.get_text() or "انلاین" in tag.get_text() or "last online" in tag.get_text().lower()))
            if lastonline_th:
                lastonline_td = lastonline_th.find_next_sibling('td')
                if lastonline_td:
                    data["lastonline"] = lastonline_td.get_text(strip=True)
            
        # Extract links from <textarea id="subscription-links">
        textarea_tag = soup.find('textarea', id='subscription-links')
        links = []
        if textarea_tag:
            links_text = textarea_tag.text.strip()
            if links_text:
                # 3x-ui separates links by newlines or carriage returns
                raw_links = [link.strip() for link in links_text.split('\n') if link.strip()]
                # Filter out empty ones
                links = [link for link in raw_links if link]
                
        return render_template('index.html', data=data, links=links)
        
    except Exception as e:
        app.logger.error(f"Error fetching subscription data: {str(e)}")
        return render_template('404.html'), 404

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
