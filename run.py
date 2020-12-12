from MelonPlyBuilder import *
from TitleBasedPlyGenerator import *

dir = 'arena_data'

ply_generator = TitleBasedPlyGenerator(dir)
ply_generator.set_default()

title = input("오늘은 이런 노래가 땡긴다 (~v~)/ : ")
rec_songs, extracted_tags, rec_tags = ply_generator.title_based_recommend(title, topk = 50)
play_list = [title] + ply_generator.convert_to_name(rec_songs)

ply_generator = MelonPlyBuilder()
ply_generator.login(input("Insert your Melon ID : "), input("Insert your Melon pwd : "))
ply_generator.run(play_list)
ply_generator.logout()
ply_generator.quit()