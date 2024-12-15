import librosa
import numpy as np
import onnxruntime
import sys
"""
input the separated audio wave file in 2 channels
return an string of class of sound
"""

def load_wave_data(path):
    x, fs = librosa.load(path, sr=48000)
    return x, fs

def calculate_melsp(x, n_fft=1024, hop_length=128):
    stft = np.abs(librosa.stft(x, n_fft=n_fft, hop_length=hop_length))**2
    log_stft = librosa.power_to_db(stft)
    melsp = librosa.feature.melspectrogram(S=log_stft,n_mels=128)
    return melsp

def Sound_classification(path, model_path):
    x, fs = load_wave_data(path)
    melsp = calculate_melsp(x)
    #print("wave size:{0}\nmelsp size:{1}\nsamping rate:{2}".format(x.shape, melsp.shape, fs))
    if 1723 - melsp.shape[1] > 0:
        z = np.zeros((128, (1723 - melsp.shape[1])))
        melsp = np.append(melsp, z, axis=1)
    else:
        melsp = melsp[:,:1723]
    melsp = np.reshape(melsp, (1, 128, 1723))
    #print(melsp.shape)

    """
    make inference with .onnx model
    """
    model_path = model_path
    sess = onnxruntime.InferenceSession(model_path)
    input_name = sess.get_inputs()[0].name
    label_name = sess.get_outputs()[0].name
    pred = sess.run([label_name], {input_name: melsp.astype(np.float32)})[0]

    labels = ["Animal", "Nature", "Human", "Domestic", "Urban"]
    return labels[np.argmax(pred) // 10]

if __name__ == "__main__":
    if len(sys.argv) == 2:
        file_name = sys.argv[1]
        print(Sound_classification("./wav/"+file_name, './model/net.onnx'))
    else:
        print(Sound_classification("./wav/Urban.wav", './model/net.onnx'))