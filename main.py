import os
import signal
from time import sleep
import pickle

import scrappers as s


class GracefulKiller:
    kill_now = False

    def __init__(self):
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, signum, frame):
        self.kill_now = True


class QueueAndArchive:
    def __init__(self):
        work_dir = os.path.dirname(os.path.realpath(__file__))

        self._hashes_local = os.path.normpath('{}/hashes.db'.format(work_dir))
        self._old_articles_local = os.path.normpath('{}/old_articles.db'.format(work_dir))

        self._queue = []

        try:
            with open(self._hashes_local, 'rb') as f:
                self.hashes = pickle.load(f)
        except FileNotFoundError:
            self.hashes = {}

            with open(self._hashes_local, 'wb') as f:
                pickle.dump(self.hashes, f)

        try:
            with open(self._old_articles_local, 'rb') as f:
                self.old_articles = pickle.load(f)
        except FileNotFoundError:
            self.old_articles = {}

            with open(self._old_articles_local, 'wb') as f:
                pickle.dump(self.old_articles, f)

    def handle_results(self, site, results, hash_):
        self._queue += results
        self.hashes[site] = hash_

    def send_and_clear(self):
        for i, article in enumerate(self._queue):
            site = article['site']

            # TO-DO Add telegram msg sender
            print(f"*{article['msg']}*:\n"
                  f"[{article['url']}]({article['title']})")

            if not self.old_articles.get(site):
                self.old_articles[site] = []

            self.old_articles[site].insert(0, article['url'])
            self.old_articles[site] = self.old_articles[site][0:100]

            self._queue.pop(i)

        self.store()

    def store(self):
        with open(self._old_articles_local, 'wb') as f:
            pickle.dump(self.old_articles, f)

        with open(self._hashes_local, 'wb') as f:
            pickle.dump(self.hashes, f)

    def get_queue(self):
        return self._queue

    def get_hash(self, site):
        return self.hashes.get(site, '')

    def get_old_articles(self, site):
        return self.old_articles.get(site, [])


if __name__ == '__main__':
    killer = GracefulKiller()
    q = QueueAndArchive()

    waiting_minutes = 30

    while not killer.kill_now:
        q.handle_results('ufop_noticias', *s.ufop_noticias(q.get_old_articles('ufop_noticias'),
                                                           q.get_hash('ufop_noticias')))

        q.handle_results('proex_noticias', *s.proex_noticias(q.get_old_articles('proex_noticias'),
                                                             q.get_hash('proex_noticias')))

        q.handle_results('propp_noticias', *s.propp_noticias(q.get_old_articles('propp_noticias'),
                                                             q.get_hash('propp_noticias')))

        q.send_and_clear()

        sleep(waiting_minutes * 60)
