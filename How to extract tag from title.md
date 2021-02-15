## :woman_technologist: 제목에서 적절한 태그를 추출하는 방법

<br></br>

word2vec으로 학습된 단어(이하 tag)를 이용해서 잘 어울리는 노래를 찾아줄 것이다.

제목을 적절히 embedding해서, 유사한 embedding을 갖는 playlist를 찾아내야한다. 즉 제목에서 tag를 추출해야 한다!

<br></br>

내가 원하는 흐름은 다음과 같다.

1. 사용자가 입력한 제목 : `잔잔한새벽에드라이브하며 듣고 싶은 몽롱한 분위기의 팝`
2. 제목에서 추출한 태그 : `잔잔한` ,  `새벽` , `드라이브` , `몽롱한` , `팝`
    - 조건 : 띄어쓰기가 되어있지 않아도 잘 추출할 수 있어야 한다.
3. `title embedding = v_잔잔한 + v_새벽 + v_드라이브 + v_몽롱 + v_팝`

<br></br>그런데 2번 과정이 생각보다 쉽지 않았다 !!

스윽 보기에는 '그냥 vocab에 있는 부분만 추출하면 되는거 아니야?'싶지만, 원하는대로 깔끔하게 추출하는 것이 쉽지 않다.

- `잔잔한새벽에드라이브하며` 에서 `라이브` 도, `이브` 도 아닌 `드라이브` 만을 추출하기 위해서는 어떤 규칙을 알려줘야 할까?
- 만약 추출한 결과가 `몽롱한` `노래` 라면, 또한 추출한 결과 중에서 사용자의 의도와 잘 맞는 단어, 더 힘을 실어주어야 할 단어는 무엇일까?

이를 구현하기 위해 고민했던 부분을 기술할 것이다. 🧐

<br></br>

---

<br></br>

### **0 ) Trie를 이용해서 base line만들기**

vocab에 있는 태그는 총 96,640개로 약 10만개이다.

입력한 단어가 vocab에 있는지를 빠르게 검사하기 위해서는 `word in vocab` 보다 효율적인 방법을 사용해야 한다.

그래서 trie 구조를 이용해서 `TagExtractor` 라는 class를 생성했다.

`in` 연산을 이용하면 `O(N)` 이 소요되지만, trie를 이용해서 tree 구조를 생성하면 `O(logn)` 만에 탐색할 수 있다.

```python
class TagExtractor:
    def __init__(self):
        self.head = Node(None)

    def insert(self, query):
				"""query를 trie에 입력한다."""

    def search(self, query):
				"""query가 trie에 있는지 검사한다. return True or False"""

    def extract(self, query):
				"""query에서 trie에 있는 tag를 추출한다. return list"""
```

<br></br>

### **1 ) 아~주 심플하게 만들어보기**

1. 입력한 제목을 공백으로 자른다. `잔잔한새벽드라이브하며` , `듣고` , `싶은` , `몽롱한` , `분위기의` , `팝`
2. 잘려진 단어가 vocab에 있는지 확인한다.
3. vocab에 있는 tag만 추출한다.

이를 코드로 나타내면

```python
def extract(self, query):
    tags = []
    for word in query.split():
        if self.search(word):
            tags.append(word)
    return tags
```

<br></br>**이 방법의 단점은 무엇일까?**

띄어쓰기나 이어붙여진 다른 단어 때문에 추출되지 않을 수 있다는 것!

- `잔잔한` , `새벽` , `드라이브` 는 있지만 `잔잔한새벽드라이브하며`는 없기 때문에 걸러진다.
- `분위기` 는 있지만 `분위기의` 는 없기 때문에 걸러진다.

trie의 search 연산은 기본적으로 같은 prefix를 가지는 단어가 있는지를 체크하다가, 없으면 False를 return하기 때문에 이러한 현상이 발생한다.

<br></br>

### 2 ) search method를 고쳐보는건 어떨까?

`잔잔한새벽` 에서 `잔잔한` 마저도 찾지 못하는 이유는, `잔잔한새` 를 prefix로 갖는 단어가 없기 때문!

그렇다면 **일단 최대한 매칭**시킨 후에, **더 이상 매칭시킬 수 없는 node에서 모든 자식 node의 value를 return**하게 만드는건 어떨까?

- `잔잔한새벽` 에서 `Node(잔잔한)` 까지 탐색한 후에 `잔잔한분위기` `잔잔한느낌` `잔잔한노래들` 을 모두 가져온다.
- `분위기의` 에서 `Node(분위기)` 까지 탐색한 후에 `분위기` `분위기짱짱` 을 모두 가져온다.

<br></br>

이 예제만 보면 나쁘지 않아보인다 !

그러나 막상 실행시켜보면 **같은 prefix에서 파생된 단어라고 해서 모두 비슷한 결을 갖는 것은 아님을 알 수 있다 !!**

- `아이를위한동요` 에서 위 방법으로 태그를 추출한다면 어떻게 될까?
- `Node(아이)` 까지 찾은 후에, `아이를` 이라는 단어는 없기 때문에 `Node(아이)` 의 모든 자식 node의 value를 찾아 가져올 것이다.
- 엉뚱하게도 `아이유`  `아이콘`  `아이폰`  `아이튠즈` 등이 출력된다.

<br></br>

내가 입력한 `아이를` 과 출력된 `아이유` 가 전혀 관련이 없는 단어라는 것을 어떻게 알려줄 수 있을까?

부모 노드 `아이` 의 embedding과 `아이유` 의 embedding의 simliarity를 비교해보는 등의 방법으로 걸러낼 수도 있겠지만 ... 자식 노드에서 출력할 수 있는 단어가 한 두개가 아니라면 골치 아픈일이 된다. 

<br></br>

### 3 ) extract를 개선해보자.

`잔잔한새벽드라이브` 에서 `잔잔한` , `새벽` , `드라이브` 를 모두 추출할 수 있으려면?

내가 생각한 조건은 다음과 같다.

1. prefix가 없다고 search를 멈추면 안된다.
    - `잔잔한` 이 vocab에 없더라도, `새벽` 과 `드라이브` 를 찾기 위해 query가 끝날 때까지 search를 계속해야한다.
2. 단어를 찾았다고 search를 멈추면 안된다.
    - `잔잔한` 을 찾고 나서 `새벽` 을 찾기 위해 search를 계속해야한다.

이를 위해 two pointer 방법으로 extract를 개선하였다.

```python
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
```

<br></br>

### 4 ) 최대 매칭 v.s. 모든 매칭

extract에는 `biggest_token` 변수가 있다.

이는 모든 매칭을 찾을 것인지, 또는 최대한 매칭되는 token을 찾을 것인지와 관련된 함수이다.

실행시켜보면 다음과 같다.

```python
'편집샵 주인장 플레이리스트 훔쳐왔다 !!!!'

최대 매칭 ['편집샵', '주인', '플레이리스트', '왔다']
모든 결과 ['편집', '편집샵', '주인', '플레이', '플레이리스트', '레이', '이리', '리스트', '왔다']
```

```python
'해변가로 드라이브 떠나고 싶다.'

최대 매칭 ['해변가', '드라이브', '떠나고', '싶다']
모든 결과 ['해변', '해변가', '드라이', '드라이브', '라이', '라이브', '이브', '떠나', '떠나고', '나고', '싶다']
```

```python
'비오는 날에 듣고싶은 쓸쓸한 발라드'

최대 매칭 ['비오는', '날에', '듣고싶은', '쓸쓸한', '발라드']
모든 결과 ['비오는', '오는', '날에', '듣고', '듣고싶은', '싶은', '쓸쓸', '쓸쓸한', '발라', '발라드']
```

```python
'아이유 노래만 모아모아'

최대 매칭 ['아이유', '노래만', '모아모아']
모든 결과 ['아이', '아이유', '이유', '노래', '노래만', '모아', '모아모아', '모아']
```

```python
'또 월요일이라니...출근길 지하철에서 듣고 싶은 노래들'

최대 매칭 ['월요일이', '출근길', '지하철에서', '듣고', '싶은', '노래들']
모든 결과 ['월요일', '월요일이', '일이', '출근', '출근길', '지하철', '지하철에서', '에서', '듣고', '싶은', '노래', '노래들']
```

척 보기에도 `모든 매칭` 은 noise가 너무 많은 것을 알 수 있다.

"드라이브"만 뽑는 것이 적절한데, '드라이', '드라이브', '라이', '라이브', '이브' 처럼 필요없는 태그까지 추출하고 있다 ! 최대한 매칭시킨 tag만을 return하도록 하자.

<br></br>

---

<br></br>

### `.insert` vocab에 단어 등록하기

영어의 경우, 대소문자가 달라지면 다르게 인식된다, 아무런 처리를 하지 않고 그냥 등록하면 `pop, Pop, POP`은 각각 다른 단어로 등록된다.

그러므로 tree를 생성할 때는 소문자로 변환하고, terminal node가 가지는 단어는 입력 단어 그대로 가지도록 한다.

예를 들어 비어있는 tree에 `Pop`을 등록하면, 다음처럼 tree의 생성은 소문자로, `is_terminal`에는 원 태그 그대로 들어가도록 한다.

```python
Head Node
└ ('p', is_terminal = False)
	└ ('o', is_terminal = False)
		└ ('p', is_terminal = 'Pop')
```

<br></br>

### `.convert` vocab에 속한 단어로 변환하기

`.insert` 를 수정했기 때문에 대소문자에는 영향이 없다.

그래서 `christmas에 딱 맞는 잔잔한 노래` 에 `.extract`를 적용하면 `self.search('christmas') == True` 가 되므로 `[christmas, 잔잔한, 노래]` 를 return할 것이다.

이대로 학습 데이터에 넣게 되면, 모델은 `Christmas`와 `christmas`를 각각 학습하게 된다. 그러나 대소문자만 다른 단어를 굳이 각각 학습할 필요가 없다!

그러므로 태그를 추출한 후에, 기존 vocab에 있는 형태로의 변환이 필요하다. 그래서 `.convert`함수를 만들었다!

```python
# example
vocab: ['Christmas', 'Jazz', '잔잔한']
query : 'christmas에 딱 맞는 잔잔한 jAZZ'
return : ['Christmas', '잔잔한', 'Jazz']
```

<br></br>

## 💻 최종 코드

```python
class TagExtractor:
    """
    vocab에 들어있는 단어만을 추출한다.
    """
    def __init__(self, limit = 2):
        self.head = Node(None)
        self.limit = limit

    def build_by_vocab(self, words):
        for word in words:
            self.insert(word, self.limit)

    def build_by_w2v(self, w2v_model_path):
        with open(w2v_model_path, 'rb') as f:
            w2v_model = pickle.load(f)

        for word in w2v_model.wv.vocab.keys():
            self.insert(word, self.limit)

    def not_satisfied(self, query, limit = 1):
        """
        숫자 또는 알파벳 한글자(의미가 부족한 태그라고 판단)는 False를 return합니다.
        limit이 1 이하인 경우에는 한글의 경우 True를 return합니다. (봄, 팝 등의 태그를 위해)
        limit이 2 이상인 경우에는 길이만을 고려합니다.
        """
        if query.isdigit():
            return True
        if limit <= 1:
            return len(query) <= limit and query.encode().isalpha()
        return len(query) < limit

    def insert(self, query, limit):
        if self.not_satisfied(query, limit):
            return

        curr_node = self.head

        for q in query.lower():
            if curr_node.children.get(q) is None:
                curr_node.children[q] = Node(q)
            curr_node = curr_node.children[q]
        curr_node.is_terminal = query

    def search(self, query, return_value = False):
        curr_node = self.head

        for q in query.lower():
            curr_node = curr_node.children.get(q)
            if curr_node is None:
                return False

        if curr_node.is_terminal:
            if return_value:
                return curr_node.is_terminal
            return True
        return False

    def extract(self, query, biggest_token=True):
        """
        vocab : 잔잔한, 감성
        input : 잔잔한감성 입니당
        return : [ 잔잔한 , 감성 ]
        """
        start, end = 0, 0
        query = query.lower() + '*'
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

    def convert(self, query, merged = False):
        """
        vocab : Christmas, 잔잔한, 감성
        input : christmas 잔잔한감성 입니당
        extracted : [ Christmas, 잔잔한 , 감성 ] ( if merged == True, '잔잔한감성' 자체가 vocab에 없으므로 추가. )
        return : [ Christmas, 잔잔한 , 감성 , 입니당 ] ( if merged == True, [ Christmas, 잔잔한, 감성, 잔잔한감성, 입니당 ] )
        """
        res = []
        for q in query.split():
            extracted = self.extract(q)
            if extracted:
                res.extend(extracted)
                if merged and not self.search(q):
                        res.append(q.lower())
            else:
                if not self.not_satisfied(q, self.limit):
                    res.append(q)

        return res
```



---

<br></br>

### 🙋여담 : 왜 형태소 분석기는 사용하지 않았는가?

`월요일이, 월요일에, 월요일`을 형태소 분석기를 통해 `월요일`로 통일해서 trie에 입력하면 훨씬 편해질 수도 있다. (애초에 w2v를 학습할 때 형태소 분석기를 통해 더 예쁘게 정제해서) 입력되는 제목 역시 형태소 분석기로 쪼개볼 수도 있다. 

<br></br>

하지만 사용하지 않은 이유는 ...

1. 만족할만한 형태소 분석기를 찾지 못했다.
    - khaiii와 한나눔 등을 사용해보았는데 랜덤, 플레이리스트 등의 영어나 아이유, 크러쉬 등 고유명사를 잘 잡아내지 못했다.
2. `태그 == 최소 단위` 라고 말하기 어렵다.
    * 만약 형태소 분석을 이용한다면, `감성힙합`은 `감성`과 `힙합`으로 쪼개질 것이다.
    * `감성 + 힙합`으로 `감성힙합`을 잘 표현해내는 것도 중요하지만, `감성힙합` 자체가 하나의 고유명사가 될 수 있다고 생각하였다.
3. vocab이 완벽하지 않더라도, 적절한 단어를 추출해낼 수 있는 프로그램을 만들어보고 싶었다.
    - 2번에서 말한 것처럼, 태그는 최소 단위가 아닌 경우가 많다. ex : `#아이유노래모음`, `#감성힙합`, `#비오는날`
    - 그래서 사용자들이 자주 쓰는 태그로 vocab을 만들게 되면, vocab은 완벽하지 않다. (형태소가 아니다.)
    - 이렇듯 완벽한 vocab이 아니더라도 적절한 추출을 할 수 있도록 만들고 싶었다.
    - 또한 사용자의 입력 역시 완벽하지 않은 경우가 많다. (띄어쓰기를 하지 않거나, 중간에 특수 문자를 끼워넣거나 등) 이 경우에서도 적절한 추출을 하기 위해서는 어떻게 설계해야할지 스스로 만들어보고 싶었다!

