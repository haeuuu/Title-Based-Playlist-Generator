import re
from tqdm import tqdm
from itertools import chain

from .util import load_json
from .extract_tags import TagExtractor

class Vocab:
    def __init__(self, train_data = '../data/train.json', limit = 2) -> None:
        self.data = load_json(train_data)
        self.build_vocab(limit = limit)

    def build_vocab(self, limit):

        print('Build Vocab ...')
        self.id_to_songs = {}
        self.id_to_tags = {}
        self.id_to_title = {}
        self.corpus = {}

        self.filter = TagExtractor(limit)
        self.filter.build_by_vocab(set(chain.from_iterable([ply['tags'] for ply in self.data])))

        for ply in tqdm(self.data):
            pid = str(ply['id'])
            self.id_to_songs[pid] = [*map(str, ply['songs'])]  # list
            self.id_to_tags[pid] = [*map(str, ply['tags'])]  # list

            raw_title = re.findall('[0-9a-zA-Z가-힣]+' ,ply['plylst_title'])
            extracted_tags = self.filter.convert(" ".join(raw_title))
            self.id_to_title[pid] = extracted_tags
            ply['tags'] = set(self.id_to_title[pid] + ply['tags'])

            self.corpus[pid] = self.id_to_songs[pid] + self.id_to_tags[pid] + self.id_to_title[pid]

        self.songs = set(chain.from_iterable(self.id_to_songs.values()))
        self.tags = set(chain.from_iterable(list(self.id_to_tags.values()) + list(self.id_to_title.values())))