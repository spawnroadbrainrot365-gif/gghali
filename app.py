from flask import Flask, request, send_file
import os
import zipfile
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import io
import time

app = Flask(__name__)


def download_website(base_url, max_files=50):
    visited = set()
    files_content = {}

    parsed_base = urlparse(base_url)
    base_domain = f"{parsed_base.scheme}://{parsed_base.netloc}"

    try:
        response = requests.get(base_url, timeout=15, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        all_links = []

        for a in soup.find_all('a', href=True):
            link = urljoin(base_url, a['href'])
            if base_domain in link:
                all_links.append(link)

        for img in soup.find_all('img', src=True):
            all_links.append(urljoin(base_url, img['src']))

        for link_tag in soup.find_all('link', href=True):
            all_links.append(urljoin(base_url, link_tag['href']))

        for script in soup.find_all('script', src=True):
            all_links.append(urljoin(base_url, script['src']))

        all_links = list(set(all_links))[:max_files]

        for i, link in enumerate(all_links):
            if link in visited:
                continue
            visited.add(link)

            try:
                time.sleep(0.1)
                file_response = requests.get(link, timeout=10, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })

                if file_response.status_code == 200:
                    file_path = urlparse(link).path
                    file_name = os.path.basename(file_path) or f"file_{i}.html"
                    files_content[file_name] = file_response.content
            except Exception:
                continue

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for file_name, content in files_content.items():
                zip_file.writestr(file_name, content)

        zip_buffer.seek(0)
        return zip_buffer, len(files_content)

    except Exception as e:
        return None, str(e)


@app.route('/')
def index():
    return send_file('index.html')


@app.route('/download', methods=['POST'])
def download():
    url = request.form.get('url', '').strip()

    if not url:
        return "الرجاء إدخال رابط صحيح", 400

    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    zip_buffer, count = download_website(url)

    if zip_buffer is None:
        return f"خطأ: {count}", 400

    return send_file(
        zip_buffer,
        mimetype='application/zip',
        as_attachment=True,
        download_name='website_files.zip'
    )


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
