import os
import torch
from pydub import AudioSegment
from pydub.playback import play

device = torch.device('cpu')
torch.set_num_threads(4)
local_file = 'v3_en.pt'

if not os.path.isfile(local_file):
    torch.hub.download_url_to_file('https://models.silero.ai/models/tts/en/v3_en.pt',
                                   local_file)

model = torch.package.PackageImporter(local_file).load_pickle("tts_models", "model")
model.to(device)

example_text = '''It could not have been ten seconds, and yet it seemed a long time that their hands were clasped together. 
He had time to learn every detail of her hand.
He explored the long fingers, the shapely nails, the work-hardened palm with its row of callouses, the smooth flesh under the wrist.
Merely from feeling it he would have known it by sight.
In the same instant it occurred to him that he did not know what colour the girl's eyes were.
They were probably brown, but people with dark hair sometimes had blue eyes.
To turn his head and look at her would have been inconceivable folly.
With hands locked together, invisible among the press of bodies,
they stared steadily in front of them, and instead of the eyes of the girl, the eyes of the aged prisoner gazed mournfully at Winston out of nests of hair.
'''
sample_rate = 8000
speaker='en_0'

current_dir = os.getcwd()
audio_path = os.path.join(current_dir, 'output.wav')

model.save_wav(text=example_text,
               speaker=speaker,
               sample_rate=sample_rate,
               audio_path=audio_path)

audio = AudioSegment.from_file(audio_path, format="wav")
play(audio)
