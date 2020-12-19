from MelonPlyBuilder import *
from TitleBasedPlyGenerator import *

dir = r'C:\Users\haeyu\PycharmProjects\KakaoArena\arena_data\model'

""" Examples : 청량한 여름, 듣고 싶은 노래들 / 편집샵 주인장 플레이 리스트 훔쳐왔다 !!! / 재즈 속에서 와인 한 잔 """
title = input("오늘은 이런 노래가 땡긴다 (~v~)/ : ")

ply_generator = TitleBasedPlyGenerator(dir)
ply_generator.set_default()
rec_songs, extracted_tags, rec_tags = ply_generator.title_based_recommend(title, topk = 30)
play_list = [title] + ply_generator.convert_to_name(rec_songs)

ply_generator = MelonPlyBuilder()
uid, password = input("Insert your Melon ID : "), input("Insert your Melon pwd : ")
ply_generator.login(uid, password)
ply_generator.run(play_list)
ply_generator.logout()
ply_generator.quit()