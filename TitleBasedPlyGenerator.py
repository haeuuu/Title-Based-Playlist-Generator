from itertools import combinations
from collections import Counter
from gensim.parsing.preprocessing import preprocess_string, strip_punctuation,remove_stopwords, stem_text,strip_multiple_whitespaces
from extract_tags import *
from Playlist2Vec import *
import os
import pandas as pd
import time

class TitleBasedRecommender(Playlist2Vec):
    def __init__(self, train_path, val_path, w2v_model):
        super().__init__(train_path, val_path)
        self.title = {str(ply['id']):ply['plylst_title'] for ply in self.data}
        self.register_w2v(w2v_model)
        self.tag_extractor = TagExtractor()
        self.tag_extractor.build_by_w2v(w2v_model)
        self.load_song_meta()

    def load_song_meta(self, song_meta_path):
        print("Load Song meta ...")
        self.song_meta = pd.read_pickle(song_meta_path)

    def build_p2v(self, mode='consistency'):
        """
        TitleBasedRecommend.build_p2v uses only tag information.

        :param normalize_tag: if True, tag embedding will be divided sum of scores.
        :param normalize_title: if True, title embedding will be divided sum of scores.
        :param song_weight: float
        :param tag_weight: float
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

            ply_embedding += self.get_weighted_embedding(items=tags, scores=tags_score)

            if type(ply_embedding) != int:  # 한 번이라도 update 되었다면
                pids.append(str(pid))  # ! string !
                playlist_embedding.append(ply_embedding)

        self.p2v_model = WordEmbeddingsKeyedVectors(self.w2v_model.vector_size)
        self.p2v_model.add(pids, playlist_embedding)

        print(f'> running time : {time.time() - start:.3f}')
        print(f'> Register (ply update) : {len(pids)} / {len(self.id_to_songs)}')
        val_ids = set([str(p["id"]) for p in self.val])
        print(
            f'> Only {len(val_ids - set(pids))} of validation set ( total : {len(val_ids)} ) can not find similar playlist in train set.')

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

    def convert_to_name(self, sid_list):
        selected = self.song_meta.loc[sid_list]
        song_name = selected['song_name']
        artist = selected['artist_name_basket'].map(lambda x: " ".join(x))
        return ( song_name + ' ' + artist ).tolist()

    def recommend(self, title, topn = 30, topn_for_songs = 50, topn_for_tags = 90, verbose = True , biggest_token = True, nouns = False, mode = 'consistency'):
        extracted_tags = self.extract_tags(sentence = title, verbose = verbose,biggest_token = biggest_token,  nouns = nouns)
        if mode == 'consistency':
            tags_score = [self.consistency[tag] for tag in extracted_tags]
        else:
            # raise NotImplementedError
            tags_score = [1]*len(extracted_tags)

        ply_embedding = self.get_weighted_embedding(extracted_tags, normalize = False, scores = tags_score)

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
            print(f"🧸 {' + '.join(extracted_tags)} !! 자, 플레이 리스트 채워왔어요 !")
            print(f"💖 #{' #'.join(tag_most_common[:15])}")
            print(self.song_meta.loc[song_most_common[:15]])
            print()
            print('🧸 이런 플레이 리스트는 어때요 ?')
            cid = str(ply_candidates[0][0])
            print(f'🎵 Title : {self.title[cid]}')
            print(f"💛 #{' #'.join(self.id_to_tags[cid])}")
            print(self.song_meta.loc[self.id_to_songs[cid][:10]])

        return song_most_common[:topn], tag_most_common

if __name__ == '__main__':
    import pickle

    dir = r'C:\Users\haeyu\PycharmProjects\KakaoArena\arena_data'
    mode = 'bm25'

    train_path = os.path.join(dir, 'orig', 'train.json')
    val_que_path = os.path.join(dir, 'questions', 'val_question.json')
    song_meta_path = os.path.join(r'C:\Users\haeyu\PycharmProjects\KakaoArena\arena_data\model','song_meta_sub.pkl')

    with open(os.path.join(dir, 'model', 'w2v_128.pkl'), 'rb') as f:
        w2v_model = pickle.load(f)

    ply_generator = TitleBasedRecommender(train_path, val_que_path, w2v_model)
    ply_generator.load_song_meta(song_meta_path)
    ply_generator.build_p2v(mode = mode)

    rec_songs, rec_tags = ply_generator.recommend(title,topn = 30, mode = mode)
    play_list = [title] + ply_generator.convert_to_name(rec_songs)