import urllib.request, re, html, sys, webbrowser
ua='Mozilla/5.0'
url='https://www.bulkammo.com/handgun'
req=urllib.request.Request(url, headers={'User-Agent': ua})
html_text=urllib.request.urlopen(req, timeout=20).read().decode('utf-8','ignore')
# find anchor tags
links=re.findall(r'<a[^>]+href="(/[^\"]+)"[^>]*>([^<]+)</a>', html_text, re.IGNORECASE)
for href, title in links:
    unescaped=html.unescape(title).strip()
    if '1000' in unescaped and 'Winchester' in unescaped and '124' in unescaped:
        print(unescaped)
        print('https://www.bulkammo.com'+href)
        sys.exit(0)
print('Product not found') 