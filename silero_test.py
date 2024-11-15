import os
import torch
from pydub import AudioSegment
from pydub.playback import play

device = torch.device('cpu')
torch.set_num_threads(4)
local_file = 'v4_ru.pt'

if not os.path.isfile(local_file):
    torch.hub.download_url_to_file('https://models.silero.ai/models/tts/ru/v4_ru.pt',
                                   local_file)

model = torch.package.PackageImporter(local_file).load_pickle("tts_models", "model")
model.to(device)

example_text = 'В недрах тундры выдры в г+етрах т+ырят в вёдра ядра кедров.'
sample_rate = 48000
speaker='baya'

current_dir = os.getcwd()
audio_path = os.path.join(current_dir, 'output.wav')
model.save_wav(text=example_text,
               speaker=speaker,
               sample_rate=sample_rate,
               audio_path=audio_path)

audio = AudioSegment.from_wav(audio_path)
play(audio)
