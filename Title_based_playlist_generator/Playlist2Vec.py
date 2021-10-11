import os
import time
import pickle
import numpy as np

from tqdm import tqdm
from collections import Counter, defaultdict

from .vocab import Vocab
from .weighted_ratings import Ratings

from gensim.models import Word2Vec
from gensim.models.keyedvectors import KeyedVectors

class Song2Vec:
    def __init__(self, train_path, w2v_path, limit = 2):
        self.vocab = Vocab(train_path, limit)
        print("> Corpus :", len(self.vocab.corpus))
        print(f'> Songs + Tags = {len(self.vocab.songs)} + {len(self.vocab.tags)} = {len(self.vocab.songs) + len(self.vocab.tags)}')

        if os.path.isfile(w2v_path):
            self.register_song2vec(w2v_path)
        else:
            self.train_song2vec(save_to = w2v_path)

    def register_song2vec(self, w2v_model_path):
        print(f'Load song2vec from {w2v_model_path}...')
        with open(w2v_model_path, 'rb') as f:
            self.w2v_model = pickle.load(f)

    def train_song2vec(self, min_count = 3, size = 128, window = 250, sg = 1, workers = 1, save_to = './data/w2v.pkl'):
        print('Train song2vec ...')
        start = time.time()
        self.w2v_model = Word2Vec(sentences = list(self.vocab.corpus.values()),
                                min_count = min_count,
                                size = size,
                                window = window,
                                sg = sg,
                                workers = workers)

        with open(save_to, 'wb') as f:
            pickle.dump(self.w2v_model, f)
        
        print(f'> running time : {time.time() - start:.3f}')
        print(f'> save to "{save_to}"')

class Playlist2Vec(Song2Vec):
    def __init__(self, train_path, w2v_path, p2v_path, limit = 2, mode = 'bm25', **build_p2v_params):
        super().__init__(train_path, w2v_path, limit)
        if os.path.isfile(p2v_path):
            self.register_p2v(p2v_path)
        else:
            self.build_p2v(mode = mode, save_to = p2v_path, **build_p2v_params)

    def build_bm25(self):
        """
        { pid : {
            'songs' : [ [song1, song2, ... ], [score1, score2, ... ] ],
            'tags' : [ [tag1, tag2, ...], [score1 , score2 , ...] ]
            }
        , ... }
        """
        print('Build bm25 ...')
        rating_builder = Ratings(self.vocab.data)
        ratings = rating_builder.build_coo(self.w2v_model)
        ratings_weighted = 5 * rating_builder.bm25_weight(ratings).tocsr()
        idf = rating_builder.idf_weight(ratings)

        bm25 = defaultdict(lambda: {'songs': [[], []], 'tags': [[],[]]}) 
        for pid in tqdm(self.vocab.corpus.keys()):

            target = ratings_weighted[int(pid)]
            scores = target.data
            iids = target.indices

            for iid, score in zip(iids, scores):
                if iid >= rating_builder.num_song:
                    tag = rating_builder.id2tag[iid - rating_builder.num_song]
                    bm25[pid]['tags'][0].append(tag)
                    bm25[pid]['tags'][1].append(score)
                else:
                    song = str(iid)
                    bm25[pid]['songs'][0].append(song)
                    bm25[pid]['songs'][1].append(score)

        return bm25, idf

    def build_consistency(self, topn=3):
        """
        co-occurrence를 계산하고 consistency를 얻는다!
        """

        print('Calculate co-occurrence ...')
        co_occur = defaultdict(Counter)
        for items in tqdm(self.corpus.values()):
            cnt = Counter(items)
            for curr in items:
                co_occur[curr].update(cnt)

        for tag, cnt in tqdm(co_occur.items()):
            del cnt[tag]

        print('Get consistency ...')
        consistency = {}
        for query in tqdm(co_occur.keys()):
            sims = []
            for tag, sim in co_occur[query].most_common(topn):
                try:
                    sims.append((tag, self.w2v_model.similarity(query, tag)))
                except KeyError:
                    continue

            sims_mean = sum([s for t, s in sims[:topn]]) / topn
            exp_mean = np.exp(sims_mean * 5)
            consistency[query] = exp_mean

        return consistency

    def register_p2v(self, p2v_path):
        print(f'Load playlist2vec from {p2v_path} ...')
        with open(p2v_path, 'rb') as f:
            self.p2v_model, self.weight = pickle.load(f)

    def get_weighted_embedding(self, items, normalize=True, scores=None):
        """
        items의 embedding을 scores에 따라 weighted sum한 결과를 return합니다.
        :param items: list of songs/tags
        :param normalize: if True, embedding vector will be divided by sum of scores or length of items
        :param mode: bm25 or consistency ( default : bm25 )
        :return: embedding vector
        """
        if not items:
            return 0

        if scores is None:
            scores = [1] * len(items)

        embedding = 0
        for item, score in zip(items, scores):
            embedding += score * self.w2v_model.wv.get_vector(item)

        if normalize:
            embedding /= sum(scores)

        return embedding

    def build_p2v(self, normalize_song = True, normalize_tag = True,
                  song_weight = 1, tag_weight = 1, mode = 'bm25', only_tag = False, save_to = '../data/p2v.pkl'):
        """
        :param normalize_song: if True, song embedding will be divided sum of scores.
        :param normalize_tag: if True, tag embedding will be divided sum of scores.
        :param normalize_title: if True, title embedding will be divided sum of scores.
        :param song_weight: float
        :param tag_weight: float
        """
        print(f'Build playlist2vec ...')

        start = time.time()
        pids = []
        playlist_embedding = []

        if mode == 'bm25':
            bm25, idf = self.build_bm25()
            self.weight = idf
        elif mode == 'consistency':
            consistency = self.build_consistency()
            self.weight = consistency
        else:
            songs_score = None
            tags_score = None

        for pid in tqdm(self.vocab.corpus.keys()):
            ply_embedding = 0

            if mode == 'bm25':
                songs, songs_score = bm25[pid]['songs']
                tags, tags_score = bm25[pid]['tags']
            else:
                songs = [song for song in self.vocab.id_to_songs[pid] if self.w2v_model.wv.vocab.get(song)]
                tags = [tag for tag in self.vocab.id_to_tags[pid] + self.vocab.id_to_title[pid] if self.w2v_model.wv.vocab.get(tag)]

                if mode == 'consistency':
                    songs_score = [consistency[song] for song in songs]
                    tags_score = [consistency[tag] for tag in tags]

            if not only_tag:
                ply_embedding += song_weight * self.get_weighted_embedding(songs, normalize_song, scores=songs_score)
            ply_embedding += tag_weight * self.get_weighted_embedding(tags, normalize_tag, scores=tags_score)

            if type(ply_embedding) != int:
                pids.append(str(pid))
                playlist_embedding.append(ply_embedding)

        self.p2v_model = KeyedVectors(self.w2v_model.vector_size)
        self.p2v_model.add(pids, playlist_embedding)

        print(f'> running time : {time.time() - start:.3f}')
        print(f'> registered : {len(pids)} / {len(self.vocab.id_to_songs)}')

        with open(save_to, 'wb') as f:
            pickle.dump((self.p2v_model, self.weight), f)