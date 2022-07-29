# Memproses suara
import wave
obj = wave.open("soundprocess.wav", "rb")
print(" Number of cahnells", obj.getnchannels())
print(" Sample width ", obj.getsampwidth())
print(" all parameter ", obj.getparams())