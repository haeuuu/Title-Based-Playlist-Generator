from itertools import combinations
from collections import defaultdict
from gensim.parsing.preprocessing import preprocess_string, strip_punctuation,remove_stopwords, stem_text,strip_multiple_whitespaces
from extract_tags import *
from Playlist2Vec import *
import re, os
import pandas as pd
import pickle

class TitleBasedRecommender(Playlist2Vec):
    def __init__(self, train_path, val_path, w2v_model):
        super().__init__(train_path, val_path)
        self.title = {str(ply['id']):ply['plylst_title'] for ply in self.data}
        self.register_w2v(w2v_model)
        self.tag_extractor = TagExtractor()
        self.tag_extractor.build_by_w2v(w2v_model)
        self.load_song_meta()

    def load_song_meta(self):
        print("Load Song meta ...")
        self.song_meta = pd.read_pickle(os.path.join(self.dir,'song_meta_sub.pkl'))

    def extract_tags(self, sentence, verbose = True, biggest_token = True, nouns = False, vote = False):
        raw_title = preprocess_string(sentence, [remove_stopwords, stem_text, strip_punctuation, strip_multiple_whitespaces])
        extracted_tags = self.tag_extractor.extract_from_title(" ".join(raw_title), biggest_token, nouns)
        if vote:
            extracted_tags = self.vote(extracted_tags, verbose)
        return extracted_tags

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

    def top_items(self, query_items, verbose=True):
        candidates = self.w2v_model.wv.most_similar(query_items, topn=1000)
        songs = [int(item) for item, sim in candidates if item.isdigit()]
        tags = [item for item, sim in candidates if not item.isdigit()]

        if verbose:
            print('> Recommended tags  :', tags[:10])
            print('> Recommended songs :')
            print(self.song_meta.loc[songs[:15]])

        return songs, tags

    def convert_to_name(self, sid_list):
        selected = self.song_meta.loc[sid_list]
        song_name = selected['song_name']
        artist = selected['artist_name_basket'].map(lambda x: " ".join(x))
        return ( song_name + ' ' + artist ).tolist()

    def title_based_recommend(self, title, topk = 20 ,verbose=True, biggest_token=True):
        extracted_items = self.extract_tags(sentence = title, verbose = verbose, biggest_token = biggest_token)
        rec_songs, rec_tags = self.tag_based_recommend(extracted_items, topk = topk, verbose = verbose)
        return rec_songs, extracted_items, rec_tags

    def tag_based_recommend(self, tags, topk = 20 ,verbose=True):
        rec_songs, rec_tags = self.top_items(tags, verbose)

        if len(rec_songs) < topk:
            print(f'[Warning] recommended songs : {len(rec_songs)}')

        return rec_songs[:topk], rec_tags[:10]

if __name__ == '__main__':
    dir = r'C:\Users\haeyu\PycharmProjects\KakaoArena\arena_data\model'
    ply_generator = TitleBasedPlyGenerator(dir)
    ply_generator.set_default()

    rec_songs, extracted_tags, rec_tags = ply_generator.title_based_recommend('편집샵 주인장 플레이리스트 훔쳐왔다 !!!', topk = 20)
    print(ply_generator.convert_to_name(rec_songs[:5]))
