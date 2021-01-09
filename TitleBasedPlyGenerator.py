from itertools import combinations
import re, os
import pandas as pd
import pickle
from konlpy.tag import Hannanum

class Node:
    def __init__(self, value):
        self.value = value
        self.children = {}
        self.is_terminal = False

class Node:
    def __init__(self, value):
        self.value = value
        self.children = {}
        self.is_terminal = False

class Trie:
    def __init__(self, w2v_model):
        self.w2v_model = w2v_model
        self.head = Node(None)

        print("********* DB 구성중입니다 *********")
        for word in w2v_model.wv.vocab.keys():
            if word.isdigit():
                continue
            word = ''.join(self.resub(word))
            if word:
                self.insert(word)
        print("************ 입력 완료 ************")

    def resub(self, query):
        return re.findall('\w+', query)

    def insert(self, query):
        if len(query) <= 1:
            return

        curr_node = self.head

        for q in query:
            if curr_node.children.get(q) is None:
                curr_node.children[q] = Node(q)
            curr_node = curr_node.children[q]
        curr_node.is_terminal = query

    def search(self, query):
        curr_node = self.head

        for q in query:
            curr_node = curr_node.children.get(q)
            if curr_node is None:
                return False

        if curr_node.is_terminal:
            return True
        return False

    def extract(self, query, biggest_token = True):
        start, end = 0,0
        query += '*'
        curr_node = self.head
        prev_node = self.head

        extracted_tags = []
        while end < len(query):
            curr_node = curr_node.children.get(query[end])
            if curr_node is None:
                if biggest_token and prev_node.is_terminal:
                    extracted_tags.append(prev_node.is_terminal)
                    start = end-1
                    prev_node = self.head
                start += 1
                end = start
                curr_node = self.head
            else:
                if not biggest_token and curr_node.is_terminal:
                    extracted_tags.append(curr_node.is_terminal)
                elif curr_node.is_terminal:
                    prev_node = curr_node
                end += 1

        return  extracted_tags

    def extract_from_title(self, title, biggest_token = True):
        tags = []
        for word in title.split():
            tags.extend(self.extract(word,biggest_token))
        return tags

    def extract_nouns(self, title):
        nouns = hannanum.nouns(" ".join(self.resub(title)))
        results = []
        for noun in nouns:
            if self.search(noun):
                results.append(noun)

        return results

class TitleBasedPlyGenerator:
    def __init__(self, dir):
        self.dir = dir

    def set_default(self):
        self.register_w2v()
        self.build_trie()
        self.load_song_meta()

    def register_w2v(self, w2v_model = None):
        print("******* Word2Vec 로드 중 *********")
        if w2v_model is None:
            with open(os.path.join(self.dir, 'w2v_128.pkl'), 'rb') as f:
                w2v_model = pickle.load(f)
        self.w2v_model = w2v_model

    def build_trie(self):
        self.trie = Trie(self.w2v_model.wv.vocab.keys())

    def load_song_meta(self):
        print("******* Song meta 로드 중 ********")
        self.song_meta = pd.read_pickle(os.path.join(self.dir,'song_meta_sub.pkl'))

    def extract_tags(self, sentence, verbose=True, biggest_token=True):
        sentence = "".join(re.findall('\w', sentence))
        extracted_tags = self.trie.extract(sentence, biggest_token)
        filtered_tags = self.filter_tags(extracted_tags, verbose)

        if verbose:
            print('> Extracted tags :', extracted_tags)
            print("> Filtered tags :", filtered_tags)

        return filtered_tags

    def filter_tags(self, tags, verbose=True):
        if len(tags) <= 2:
            return tags

        pairs = []
        for tag1, tag2 in combinations(tags, 2):
            sim = self.w2v_model.wv.similarity(tag1, tag2)
            if sim < 0.1:
                continue
            pairs.append((sim, (tag1, tag2)))

        M, m = max(sim for sim, _ in pairs), min(sim for sim, _ in pairs)
        threshold = m + 0.3 * (M - m)

        res = []
        for sim, (tag1, tag2) in pairs:
            if sim < threshold:
                continue
            res.append(tag1)
            res.append(tag2)

        if verbose:
            print('> Similarity :', [f'{tags} : {sim:.4f}' for sim, tags in pairs])
            print(f'> Threshold : {threshold:.4f}')

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
