import os
from Title_Based_Playlist_Generator import *

"""
Examples

청량한 남돌 노래만 차곡차곡
틀어놓기만 해도 해변가 드라이브 중
편집샵 주인장 플레이 리스트 훔쳐왔다!!
방구석 스타벅스 만들어주는 플레이리스트
밤에 듣기 좋은 몽롱한 분위기의 pop
마음이 몽글몽글해지는 팝송
추적추적 비내리는 창가
도입부 장난 아님

"""

dir = r'C:\Users\haeyu\PycharmProjects\KakaoArena\arena_data'
train_path = os.path.join(dir, 'orig', 'train.json')
val_path = os.path.join(dir, 'orig', 'val.json')
song_meta_path = os.path.join(dir, 'model', 'song_meta_sub.pkl')
w2v_model_path = os.path.join(dir, 'model', 'w2v_128.pkl')

mode = 'bm25'
ply_generator = TitleBasedRecommender(train_path, val_path, w2v_model_path, song_meta_path)

p2v_model_path = os.path.join(dir, 'model', f'p2v_model_{mode}.pkl')
if f'p2v_model_{mode}.pkl' in os.listdir(os.path.join(dir, 'model')):
    ply_generator.register_p2v(p2v_model_path)
else:
    ply_generator.build_p2v(mode=mode, path_to_save=dir)

ply_builder = MelonPlyBuilder()

while True:
    title = input("\n오늘은 이런 노래가 땡긴다 ~ (~v~)/ : ")
    if title == 'quit':
        print('\n이용해주셔서 감사함니다 ~ (-v-) (_ _)')
        break

    rec_songs, rec_tags = ply_generator.recommend(title, topn = 30, mode = mode)
    play_list = [title] + ply_generator.convert_to_name(rec_songs)

    if not ply_builder.login_status:
        uid, password = input("Insert your Melon ID : "), input("Insert your Melon pwd : ")
        ply_builder.login(uid, password)
    ply_builder.run(play_list) #TODO : init query

ply_builder.logout()
ply_builder.quit()