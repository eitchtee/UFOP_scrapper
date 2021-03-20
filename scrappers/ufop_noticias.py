import hashlib
from urllib3.exceptions import NewConnectionError, MaxRetryError

import requests
from bs4 import BeautifulSoup
from requests.exceptions import ConnectionError


def get_hash(field):
    noticia_hash = hashlib.sha224(field.text.encode('utf-8')).hexdigest()
    return noticia_hash


def ufop_noticias(old_articles, old_page_hash):
    msg = "Nova notícia publicada pela UFOP"
    site = "ufop_noticias"
    main_url = 'https://www.ufop.br'

    max_news_per_page = 6
    max_pages_to_fetch = 15

    main_page_hash = ''

    results = []

    page = 0
    while True:
        try:
            request = requests.get(f'https://www.ufop.br/noticias?page={page}')
        except (NewConnectionError, ConnectionRefusedError, MaxRetryError, ConnectionError) as e:
            print('UFOP Notícias: Site fora do ar.')
            continue

        soup = BeautifulSoup(request.text, 'html.parser')

        articles_field = soup.find(class_='view-content')

        new_hash = get_hash(articles_field)

        if page == 0:
            main_page_hash = new_hash

        if new_hash != old_page_hash or page != 0:
            articles_titles = soup.find_all(class_='campl-teaser-title')

            for article in articles_titles:
                article_title = article.text
                article_url = main_url + article.find('a', href=True)['href']

                if article_url not in old_articles:
                    results.append({'title': article_title, 'url': article_url, 'msg': msg, 'site': site})

            if len(results) >= max_news_per_page * (page + 1) and page <= max_pages_to_fetch:
                page += 1
            else:
                break
        else:
            break

    return results, main_page_hash
