import pickle

class Node:
    def __init__(self, value):
        self.value = value
        self.children = {}
        self.is_terminal = False

class TagExtractor:
    """
    vocab에 들어있는 단어만을 추출한다.
    """
    def __init__(self):
        self.head = Node(None)

    def build_by_vocab(self, words):
        for word in words:
            self.insert(word)

    def build_by_w2v(self, w2v_model_path):
        with open(w2v_model_path, 'rb') as f:
            w2v_model = pickle.load(f)

        for word in w2v_model.wv.vocab.keys():
            if word.isdigit():
                continue
            self.insert(word)

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

    def extract(self, query, biggest_token=True):
        start, end = 0, 0
        query += '*'
        curr_node = self.head
        prev_node = self.head

        extracted_tags = []
        while end < len(query):
            curr_node = curr_node.children.get(query[end])
            if curr_node is None:
                if biggest_token and prev_node.is_terminal:
                    extracted_tags.append(prev_node.is_terminal)
                    start = end - 1
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

        return extracted_tags

    def extract_from_title(self, title, biggest_token=True, nouns=False):
        tags = []
        if nouns:
            return self.extract_nouns(title)
        else:
            for word in title.split():
                tags.extend(self.extract(word, biggest_token))
            return tags

    def extract_nouns(self, title):
        nouns = hannanum.nouns(" ".join(self.resub(title)))
        tags = []
        for noun in nouns:
            if self.search(noun):
                tags.append(noun)

        return tags