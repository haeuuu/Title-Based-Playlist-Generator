import fire

from Title_based_playlist_generator import *
from Melon_playlist_auto_generator import *

class PlaylistGenerator:
    @staticmethod
    def run(chromedriver_path = './chromedriver',
            train_path = './data/train.json',
            w2v_model_path = './data/w2v.pkl',
            p2v_model_path = './data/p2v.pkl',
            song_meta_path = './data/song_meta.df',
            mode = 'bm25',
            test_mode = False,
            topn = 30,
            uid = None,
            pwd = None
            ):

        """
        Examples
        --------
        청량한 남돌 노래만 차곡차곡
        틀어놓기만 해도 해변가 드라이브 중
        편집샵 주인장 플레이 리스트 훔쳐왔다!!
        방구석 스타벅스 만들어주는 플레이리스트
        밤에 듣기 좋은 몽롱한 분위기의 pop
        마음이 몽글몽글해지는 팝송
        추적추적 비내리는 창가
        도입부 장난 아님
        """

        ply_generator = TitleBasedRecommender(train_path, w2v_model_path, p2v_model_path, song_meta_path, mode = mode)
        if not test_mode:
            ply_builder = MelonPlyBuilder(chromedriver_path = chromedriver_path)
            if uid is None:
                uid = input("Insert your Melon ID : ")
            if pwd is None:
                pwd = input("Insert your Melon pwd : ")
            ply_builder.login(uid, pwd)

        while True:
            title = input("\n플레이 리스트의 제목을 지어주세요 ! 🎧 ")
            if title == 'quit':
                print('\n종료할게요 ! 👋 ')
                break

            rec_songs, rec_tags = ply_generator.recommend(title, topn = topn)
            play_list = [title] + ply_generator.convert_to_name(rec_songs)

            if test_mode:
                continue

            if input('등록할까요 ? 🕺 [y/n] : ') == 'y':
                ply_builder.run(play_list)

        if not test_mode:
            ply_builder.logout()
            ply_builder.quit()

if __name__ == '__main__':
    fire.Fire(PlaylistGenerator.run)