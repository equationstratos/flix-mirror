import cloudscraper
import json
import re
from bs4 import BeautifulSoup

def sync_mirror():
    # On crée un scraper qui imite très précisément un navigateur Windows
    scraper = cloudscraper.create_scraper(
        delay=10, 
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'desktop': True
        }
    )
    
    # On ajoute des headers que Cloudflare attend obligatoirement
    scraper.headers.update({
        'Referer': 'https://www.google.com/',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    })

    base_url = "https://flemmix.best/film-en-streaming/"
    mirror_data = []
    
    print(f"[*] Tentative de connexion à {base_url}...")
    
    try:
        # On tente de récupérer la page d'accueil d'abord pour obtenir les cookies
        scraper.get("https://flemmix.best/", timeout=20)
        
        # Maintenant on tente la page des films
        response = scraper.get(base_url, timeout=20)
        
        if response.status_code == 200:
            print("[+] Succès ! Cloudflare contourné.")
            soup = BeautifulSoup(response.text, 'html.parser')
            items = soup.find_all('div', class_='mov')
            
            print(f"[+] {len(items)} films trouvés.")
            
            for item in items:
                link_tag = item.find('a', class_='mov-t')
                if not link_tag: continue
                
                title = link_tag.get_text(strip=True)
                url_page = link_tag['href']
                
                print(f"    -> Extraction : {title}")
                
                # Scraping de la page interne
                p_res = scraper.get(url_page, timeout=15)
                sources = re.findall(r"loadVideo\(['\"]([^'\"]+)['\"]\).*?>(.*?)</a>", p_res.text, re.S | re.I)
                
                clean_sources = []
                for s in sources:
                    label = re.sub(r'<[^>]+>', '', s[1]).strip()
                    clean_sources.append({'label': label or "LIEN", 'url': s[0]})
                
                mirror_data.append({
                    'title': title,
                    'url_page': url_page,
                    'thumb': item.find('img')['src'] if item.find('img') else "",
                    'sources': clean_sources
                })

            # Sauvegarde
            with open('mirror.json', 'w', encoding='utf-8') as f:
                json.dump(mirror_data, f, indent=4, ensure_ascii=False)
            print("\n[✔] Fichier 'mirror.json' prêt !")
            
        else:
            print(f"[!] Toujours bloqué : Status {response.status_code}")
            # Si ça échoue encore, on affiche un bout du code reçu pour comprendre
            print(f"DEBUG : {response.text[:200]}")
            
    except Exception as e:
        print(f"[!] Erreur : {e}")

if __name__ == "__main__":
    sync_mirror()
