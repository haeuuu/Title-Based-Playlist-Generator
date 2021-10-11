import pandas as pd
from collections import Counter

from .extract_tags import TagExtractor
from .Playlist2Vec import Playlist2Vec


class TitleBasedRecommender:
    def __init__(self,
                train_path = '../data/train.json',
                w2v_model_path = '../data/w2v.pkl',
                p2v_model_path = '../data/p2v.pkl',
                song_meta_path = '../data/song_meta.df',
                limit = 2,
                mode = 'bm25'
                ):
        self.p2v = Playlist2Vec(train_path, w2v_model_path, p2v_model_path, limit, mode, only_tag = True)

        self.title = {str(ply['id']):ply['plylst_title'] for ply in self.p2v.vocab.data}
        self.tag_extractor = TagExtractor(limit = limit)
        self.tag_extractor.build_by_w2v(w2v_model_path)
        self.song_meta = pd.read_pickle(song_meta_path)

    def convert_to_name(self, sid_list):
        selected = self.song_meta.loc[sid_list]
        song_name = selected['song_name']
        artist = selected['artist_name_basket'].map(lambda x: " ".join(x))
        return ( song_name + ' ' + artist ).tolist()

    def recommend(self, title, topn = 30, topn_for_songs = 50, topn_for_tags = 90, verbose = True, biggest_token = True):
        extracted_tags = self.tag_extractor.extract(query = title, biggest_token = biggest_token)
        tags_score = [self.p2v.weight[tag] for tag in extracted_tags]

        ply_embedding = self.p2v.get_weighted_embedding(extracted_tags, normalize = False, scores = tags_score)

        ply_candidates = self.p2v.p2v_model.similar_by_vector(ply_embedding, topn=max(topn_for_tags, topn_for_songs))
        song_candidates = []
        tag_candidates = []

        for cid, _ in ply_candidates[:topn_for_songs]:
            song_candidates.extend(self.p2v.vocab.id_to_songs[str(cid)])
        for cid, _ in ply_candidates[:topn_for_tags]:
            tag_candidates.extend(self.p2v.vocab.id_to_tags[str(cid)])

        song_most_common = [song for song, _ in Counter(song_candidates).most_common(topn)]
        tag_most_common = [tag for tag, _ in Counter(tag_candidates).most_common(15) if tag not in extracted_tags]

        if verbose:
            print()
            print(f"🧸 < {' + '.join(extracted_tags)} > 를 조합해서 플레이 리스트를 채워왔어요 ! \n")
            print(f"💖 #{' #'.join(tag_most_common[:10])}\n")
            print(self.song_meta.loc[song_most_common[:15]])
            print()
            print('🧸 이런 플레이 리스트는 어때요 ?')
            for i in range(3):
                cid = str(ply_candidates[i][0])
                print(f'\n🎵 Title : {self.title[cid]}')
                print(f"\n💛 #{' #'.join(self.p2v.vocab.id_to_tags[cid])}\n")
                print(self.song_meta.loc[self.p2v.vocab.id_to_songs[cid][:10]])
                print()

        return song_most_common, tag_most_common