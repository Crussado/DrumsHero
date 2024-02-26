import librosa
import numpy as np
import soundfile as sf
import sounddevice as sd

class Music():
    def __init__(self, file) -> None:
        self.song, self.sampling_rate = librosa.load(file)
        self.cromagrama = librosa.feature.chroma_stft(y=self.song, sr=self.sampling_rate)
        self.intervalos_tiempo = librosa.frames_to_time(range(self.cromagrama.shape[1]), sr=self.sampling_rate)
        print(len(self.cromagrama[0]), len(self.intervalos_tiempo))
        # self.ac = librosa.autocorrelate(onset)
        # tempo, other = librosa.beat.beat_track(onset_envelope=self.ac, sr=self.sampling_rate)
        self.y_harmonic, self.y_percussive = librosa.effects.hpss(self.song)
        self.tempo, self.beat_frames = librosa.beat.beat_track(y=self.y_percussive, sr=self.sampling_rate)
        self.beat_times = librosa.frames_to_time(self.beat_frames, sr=self.sampling_rate)
        self.str = librosa.onset.onset_strength(y=self.y_percussive, sr=self.sampling_rate)

        self.beat_times = librosa.frames_to_time(self.beat_frames, sr=self.sampling_rate)
        # print(len(self.beat_frames), self.beat_frames)
        # print(len(self.beat_times), self.beat_times)

    def get_vel(self):
        return self.tempo

    def get_cromagrama(self):
        return self.intervalos_tiempo, list(self.cromagrama)

    def get_events(self):
        return self.beat_times

    def mix_song(self):
        applause, sr_applause = librosa.load('./sounds/applause.mp3')
        # Asegurarse de que ambos audios tengan la misma frecuencia de muestreo
        applause = librosa.resample(applause, orig_sr=sr_applause, target_sr=self.sampling_rate)
        self.extra_time = librosa.get_duration(y=applause, sr=self.sampling_rate)
        transicion_length = 3000

        # Aplicar una ventana de Hamming a la región de transición
        ventana_transicion = np.hamming(2 * transicion_length)
        ventana_transicion = ventana_transicion[:transicion_length]

        transition_song = self.song[:transicion_length]
        transition_applause = applause[-transicion_length:]

        transition_song *= ventana_transicion
        transition_applause *= ventana_transicion

        # Unir los audios en la región de transición
        self.game_song = np.concatenate((applause[:-transicion_length], transition_applause + transition_song, self.song[transicion_length:]))

        # Guardar el audio resultante con soundfile
        # sf.write('audio_unido.wav', audio_unido, self.sampling_rate)
        self.intervalos_tiempo += self.extra_time
        self.beat_times += self.extra_time

    def play(self):
        sd.play(self.game_song, samplerate=self.sampling_rate)
'''
    song: amplitude list
    sampling_rate: number of samples per second in the song
'''
# song, sampling_rate = librosa.load(file) 
# print(f'La cancion: {len(song)}, la tasa de muestreo: {sampling_rate}')

'''
    y_harmonic, y_percussive: amplitude lists    
'''
# y_harmonic, y_percussive = librosa.effects.hpss(song)

'''
    tempo: beats per minute
    beat_frames: frame numbers corresponding to detected beat events.
'''
# tempo, beat_frames = librosa.beat.beat_track(y=song, sr=sampling_rate)
# print(f'Tempo: {tempo}, beat_frames: {beat_frames}')

'''
    beat_times: array of timestamps(in seconds) corresponding to detected beat events.
'''
# beat_times = librosa.frames_to_time(beat_frames, sr=sampling_rate)
# print('beats', beat_times)

# onset_env = librosa.onset.onset_strength(y=y_percussive, sr=sampling_rate)
# print(f'Otro: {onset_env}')

# time_segments = librosa.times_like(beat_frames, sr=sampling_rate)
# print(f'Segmentos: {time_segments}')

# cromagrama = librosa.feature.chroma_stft(y=song, sr=sampling_rate)
# print(f'Cromograma: {cromagrama}')

# ac = librosa.autocorrelate(librosa.onset.onset_strength(y=song, sr=sampling_rate))

# plt.figure()
# plt.plot(ac, label='Autocorrelación')
# plt.xlabel('Lag (frames)')
# plt.ylabel('Autocorrelation')
# plt.title(f'Compás detectado: {tempo} BPM')
# plt.legend()
# plt.savefig('compas.png')


# melodia, _ = librosa.effects.pitch_shift(y=song, sr=sampling_rate, n_steps=10)

# Visualiza la melodía
# librosa.display.waveshow(melodia, sr=sampling_rate)
# plt.title('Melodía de la canción')
# plt.savefig('melodia.png')


# tonnetz = librosa.feature.tonnetz(y=song, sr=sampling_rate)

# # Visualiza el tonnetz
# librosa.display.specshow(tonnetz, y_axis='tonnetz', x_axis='time')
# plt.colorbar()
# plt.title('Tonnetz de la canción')
# plt.savefig('tonnetz.png')
