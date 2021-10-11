import pandas as pd

song_meta = pd.read_json('./song_meta.json')
song_meta_sub = song_meta.loc[:, ['song_name','artist_name_basket']]
song_meta_sub.index = song_meta_sub.index.map(str)
pd.to_pickle(song_meta_sub, './song_meta.df')