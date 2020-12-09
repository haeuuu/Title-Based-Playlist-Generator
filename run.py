from MelonplyBuilder import *
from TitleBasedPlyGenerator import *

dir = 'arena_data'

title = input("오늘은 이런 노래가 땡긴다 (~v~)/ : ")

ply_generator = TitleBasedPlyGenerator(dir)
ply_generator.set_default()
rec_songs, extracted_tags, rec_tags = ply_generator.title_based_recommend(title, topk = 20)
play_list = [title] + ply_generator.convert_to_name(rec_songs)

ply_generator = MelonPlyBuilder()
ply_generator.login(input("Insert your Melon ID : "), input("Insert your Melon pwd : "))
ply_generator.run(play_list)
ply_generator.logout()
ply_generator.quit()