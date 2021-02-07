# TODO : build_vocab - title preprocessing, list(set(tag + title))

import os, re
import pickle
import time
import pandas as pd
from tqdm import tqdm

from collections import Counter
from itertools import combinations, chain

from .extract_tags import TagExtractor
from .Playlist2Vec import Playlist2Vec

from gensim.models.keyedvectors import WordEmbeddingsKeyedVectors
from gensim.parsing.preprocessing import preprocess_string, strip_punctuation,remove_stopwords, stem_text,strip_multiple_whitespaces

class TitleBasedRecommender(Playlist2Vec):
    def __init__(self, train_path, val_path, w2v_model_path, song_meta_path):
        super().__init__(train_path, val_path)
        self.register_w2v(w2v_model_path)
        self.tag_extractor = TagExtractor()
        self.tag_extractor.build_by_w2v(w2v_model_path)
        self.song_meta = pd.read_pickle(song_meta_path)
        self.consistency = None

    def build_vocab(self):
        self.id_to_songs = {}
        self.id_to_tags = {}
        self.id_to_title = {}
        self.corpus = {}

        for ply in tqdm(self.data):
            pid = str(ply['id'])
            self.id_to_songs[pid] = [*map(str, ply['songs'])]  # list
            self.id_to_tags[pid] = [*map(str, ply['tags'])]  # list
            self.id_to_title[pid] = ply['plylst_title']

        print('> # of Songs :', len(set(chain.from_iterable(songs for songs in self.id_to_songs.values()))))
        print('> # of Tags :', len(set(chain.from_iterable(tags for tags in self.id_to_tags.values()))))

    def register_p2v(self, p2v_model_path):
        catch_mode = re.findall('p2v_model_(\w+)', p2v_model_path)
        if not catch_mode:
            print('[ERROR] can not infer mode. available format : p2v_model_mode.pkl')
            return
        mode = catch_mode[0]

        with open(p2v_model_path, 'rb') as f:
            self.p2v_model, weight = pickle.load(f)
            setattr(self, mode, weight)

    def build_p2v(self, mode = 'consistency', path_to_save = None):
        """
        TitleBasedRecommend.build_p2v uses only tag information.
        """

        start = time.time()
        pids = []
        playlist_embedding = []

        if mode == 'bm25':
            self.build_bm25()
        elif mode == 'consistency':
            self.build_consistency()

        for pid in tqdm(self.corpus.keys()):
            ply_embedding = 0

            if mode == 'bm25':
                tags, tags_score = self.bm25[pid]['tags']
            else:
                tags = [tag for tag in self.id_to_tags[pid] + self.id_to_title[pid] if self.w2v_model.wv.vocab.get(tag)]

                if mode == 'consistency':
                    tags_score = [self.consistency[tag] for tag in tags]

            ply_embedding += self.get_weighted_embedding(items = tags, scores = tags_score)

            if type(ply_embedding) != int:  # 한 번이라도 update 되었다면
                pids.append(str(pid))  # ! string !
                playlist_embedding.append(ply_embedding)

        self.p2v_model = WordEmbeddingsKeyedVectors(self.w2v_model.vector_size)
        self.p2v_model.add(pids, playlist_embedding)

        if mode == 'bm25':
            self.bm25 = self.idf

        if path_to_save is not None:

            model_path = f'{path_to_save}/p2v_model_{mode}.pkl'
            with open(model_path, 'wb') as f:
                pickle.dump((self.p2v_model, getattr(self, mode)), f)

            print(f'> Saved in : {model_path}')

    def vote(self, tags, verbose = True):
        if len(tags) <= 2:
            return tags

        pairs = []
        for tag1, tag2 in combinations(tags,2):
            sim = self.w2v_model.wv.similarity(tag1, tag2)
            if sim < 0.1:
                continue
            pairs.append((sim, (tag1, tag2)))

        M,m = max(sim for sim, _ in pairs), min(sim for sim, _ in pairs)
        threshold = m + 0.3*(M-m)

        res = []
        for sim, (tag1, tag2) in pairs:
            if sim < threshold:
                continue
            res.append(tag1)
            res.append(tag2)

        if verbose:
            print('> sims :',pairs)
            print('> threshold :',threshold)

        return list(set(res))

    def convert_to_name(self, sid_list):
        selected = self.song_meta.loc[sid_list]
        song_name = selected['song_name']
        artist = selected['artist_name_basket'].map(lambda x: " ".join(x))
        return ( song_name + ' ' + artist ).tolist()

    def recommend(self, title, topn=30, topn_for_songs=50, topn_for_tags=90
                  , verbose=True, biggest_token=True, mode='consistency'):
        extracted_tags = self.tag_extractor.extract(query=title, biggest_token=biggest_token)
        # TODO : 추출된 태그가 없을 때 예외 처리
        if mode == 'consistency' or mode == 'bm25':
            tags_score = [getattr(self, mode)[tag] for tag in extracted_tags]
        else:
            # raise NotImplementedError
            tags_score = [1] * len(extracted_tags)

        ply_embedding = self.get_weighted_embedding(extracted_tags, normalize=False, scores=tags_score)

        ply_candidates = self.p2v_model.similar_by_vector(ply_embedding, topn=max(topn_for_tags, topn_for_songs))
        song_candidates = []
        tag_candidates = []

        for cid, _ in ply_candidates[:topn_for_songs]:
            song_candidates.extend(self.id_to_songs[str(cid)])
        for cid, _ in ply_candidates[:topn_for_tags]:
            tag_candidates.extend(self.id_to_tags[str(cid)])

        song_most_common = [song for song, _ in Counter(song_candidates).most_common()]
        tag_most_common = [tag for tag, _ in Counter(tag_candidates).most_common() if tag not in extracted_tags]

        if verbose:
            print()
            print(f"🧸 < {' + '.join(extracted_tags)} > 를 조합해서 플레이 리스트를 채워왔어요 ! \n")
            print(f"💖 #{' #'.join(tag_most_common[:15])}\n")
            print(self.song_meta.loc[song_most_common[:15]])
            print()
            print('🧸 이런 플레이 리스트는 어때요 ?')
            for i in range(3):
                cid = str(ply_candidates[i][0])
                print(f'\n🎵 Title : {self.title[cid]}')
                print(f"\n💛 #{' #'.join(self.id_to_tags[cid])}\n")
                print(self.song_meta.loc[self.id_to_songs[cid][:10]])
                print()

        return song_most_common[:topn], tag_most_common

if __name__ == '__main__':
    dir = r'C:\Users\haeyu\PycharmProjects\KakaoArena\arena_data'
    mode = 'bm25' # 'consistency'

    train_path = os.path.join(dir, 'orig', 'train.json')
    val_path = os.path.join(dir, 'orig', 'val.json') # os.path.join(dir, 'questions', 'val_question.json')
    song_meta_path = os.path.join(dir ,'model','song_meta_sub.pkl')
    w2v_model_path = os.path.join(dir ,'model','w2v_128.pkl')

    ply_generator = TitleBasedRecommender(train_path, val_path, w2v_model_path, song_meta_path)

    p2v_model_path = os.path.join(dir, 'model',f'p2v_model_{mode}.pkl')
    if f'p2v_model_{mode}.pkl' in os.listdir(os.path.join(dir,'model')):
        ply_generator.register_p2v(p2v_model_path)
    else:
        ply_generator.build_p2v(mode = mode, path_to_save = dir)

    # rec_songs, rec_tags = ply_generator.recommend('도입부 장난 아님', topn = 30, mode = mode, verbose = True)
    rec_songs, rec_tags = ply_generator.recommend('국내 인디 음악에 알앤비 한스푼', topn = 30, mode = mode, verbose = True)