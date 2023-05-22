# -*- coding: utf-8 -*-
"""Final Project Kel. 29_Coding.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/18hcYlTPSgYJUe0z35naES6UYlFfg5D4h

# load the zip file and unzip and before check the GPU
"""

from google.colab import drive
drive.mount('/content/drive')

!unzip '/content/drive/MyDrive/nitip tugas/SINYAL & SISTEM/FP/data/audiodata.zip' -d "/content/audiodata"

import tensorflow as tf
import requests, zipfile, io
from glob import glob
import matplotlib.pyplot as plt
from scipy import signal
from scipy.io import wavfile
import numpy as np
from tqdm import tqdm
import cv2
import pandas as pd
import pandas as pd
import os
import librosa

#if not os.path.exists('sound'):
   # os.makedirs('sound')

#glob('/content/audiodata/*')

#!pip install librosa
#import librosa

# label category names
df = pd.read_csv(glob('/content/drive/MyDrive/nitip tugas/SINYAL & SISTEM/FP/data/audiodata.csv')[0])
df.head(10)

my_dict = {}
for i in range(len(df)):
  my_dict[df['label'][i]] = df['jenis'][i]
my_dict

def windows(data, window_size):
    start = 0
    while start < len(data):
        yield int(start), int(start + window_size)
        start += (window_size / 2)

def extract_features(bands = 60, frames = 41):
    window_size = 512 * (frames - 1)
    log_specgrams = []
    labels = []
    for index,row in tqdm(df.iterrows()):
        name = row['filename']
        paths = os.path.join('audiodata',name)
        kind = row['jenis']
        dicti = {'hewan':0, 'kendaraan':1, 'percakapan':2, 'perabotan':3}
        label = dicti[kind]
        sound_clip,s = librosa.load(paths) # 5sec
        sound_clip   = np.concatenate((sound_clip,sound_clip),axis=None) # make it 10s
        for (start,end) in windows(sound_clip,window_size):
            if(len(sound_clip[start:end]) == window_size):
                signal = sound_clip[start:end]
                melspec = librosa.feature.melspectrogram(signal, n_mels = bands)
                logspec = librosa.core.amplitude_to_db(melspec)
                logspec = logspec.T.flatten()[:, np.newaxis].T
                log_specgrams.append(logspec)
                labels.append(label)
            
    log_specgrams = np.asarray(log_specgrams).reshape(len(log_specgrams),bands,frames,1)
    features = np.concatenate((log_specgrams, np.zeros(np.shape(log_specgrams))), axis = 3)
    for i in range(len(features)):
        features[i, :, :, 1] = librosa.feature.delta(features[i, :, :, 0])
    
    return np.array(features), np.array(labels,dtype = np.int)

features,labels = extract_features()

np.save('features.npy',features)
np.save('labels.npy',labels)

features = np.load('features.npy')
labels = np.load('labels.npy')

features.shape

labels.shape

import keras.utils

from tensorflow.keras.utils import to_categorical

onehot_labels = to_categorical(labels)

print(onehot_labels.shape)

# Create train test Dataset

rnd_indices = np.random.rand(len(labels)) < 0.80

X_train = features[rnd_indices]
y_train = onehot_labels[rnd_indices]
X_test  = features[~rnd_indices]
y_test  = onehot_labels[~rnd_indices]

X_train.shape, y_train.shape, X_test.shape, y_test.shape,

"""# CNN Model"""

from keras.models import Sequential
from keras.layers import Dense
from keras.layers import Dropout
from keras.layers import Flatten,InputLayer
from keras.layers.convolutional import Conv2D
from keras.layers.convolutional import MaxPooling2D
from keras.utils import np_utils
from tensorflow.keras.optimizers import SGD
from keras.constraints import maxnorm
from keras.callbacks import ModelCheckpoint

def basemodel():
  model = Sequential()
  model.add(Conv2D(32, (3, 3), input_shape=(60,41,2), activation='relu', padding='same'))
  model.add(Dropout(0.2))
  model.add(Conv2D(32, (3, 3), activation='relu', padding='same'))
  model.add(MaxPooling2D(pool_size=(2, 2)))
  model.add(Conv2D(64, (3, 3), activation='relu', padding='same'))
  model.add(Dropout(0.2))
  model.add(Conv2D(64, (3, 3), activation='relu', padding='same'))
  model.add(MaxPooling2D(pool_size=(2, 2)))
  model.add(Conv2D(128, (3, 3), activation='relu', padding='same'))
  model.add(Dropout(0.2))
  model.add(Conv2D(128, (3, 3), activation='relu', padding='same'))
  model.add(MaxPooling2D(pool_size=(2, 2)))
  model.add(Flatten())
  model.add(Dropout(0.2))
  model.add(Dense(1024, activation='relu', kernel_constraint=maxnorm(3)))
  model.add(Dropout(0.2))
  model.add(Dense(512, activation='relu', kernel_constraint=maxnorm(3)))
  model.add(Dropout(0.2))
  model.add(Dense(4, activation='softmax'))
  # Compile model
  epochs = 25
  lrate = 0.01
  decay = lrate/epochs
  sgd = SGD(lr=lrate, momentum=0.9, decay=decay, nesterov=False)
  model.compile(loss='categorical_crossentropy', optimizer=sgd, metrics=['accuracy'])
  return model

if not os.path.exists('model'):
    os.makedirs('model')
    
filepath="model/weights_0.best.hdf5"
checkpoint = ModelCheckpoint(filepath, monitor='val_acc', verbose=1, save_best_only=True, mode='max')
callbacks_list = [checkpoint]

model = basemodel()
print(model.summary())

from keras.preprocessing.image import ImageDataGenerator

datagen = ImageDataGenerator(
              width_shift_range=0.1,  # randomly shift images horizontally (fraction of total width)
              height_shift_range=0.1,  # randomly shift images vertically (fraction of total height)
              horizontal_flip=True,  # randomly flip images
              vertical_flip=False  # randomly flip images
          )

# init the batch size and epochs

batch_size = 50
epochs = 100

# fit the model
history = model.fit_generator(datagen.flow(X_train, y_train, batch_size=batch_size),
                              steps_per_epoch=int(np.ceil(X_train.shape[0] / float(batch_size))),
                              epochs=epochs,
                              validation_data=(X_test, y_test),
                              verbose=1,callbacks=callbacks_list)

model.save_weights('model_rev.h5')

# evaluate model
model.evaluate(X_test, y_test)

"""# Classification Report and Confusion Matrix

Confusion Matrix adalah tabel dengan 4 kombinasi berbeda dari nilai prediksi dan nilai aktual.
"""

plt.figure(figsize=(10,6))
plt.plot(history.history['loss'], label='train')
plt.plot(history.history['val_loss'], label='val')
plt.title('Loss and Validation Loss ')
plt.legend();
plt.show()

plt.figure(figsize=(10,6))
plt.plot(history.history['accuracy'], label='train')
plt.plot(history.history['val_accuracy'], label='val')
plt.title('Accuracy and Validation Accuracy')
plt.legend();
plt.show()

from sklearn.metrics import roc_auc_score, classification_report, confusion_matrix
import numpy as np
import seaborn as sns

matrix_index = ['hewan', 'kendaraan', 'percakapan', 'perabotan']

preds = model.predict(X_test)
classpreds = np.argmax(preds, axis=1) # predicted classes 
y_testclass = np.argmax(y_test, axis=1)

cm = confusion_matrix(y_testclass, classpreds)
print(classification_report(y_testclass, classpreds, target_names=matrix_index))

# Get percentage value for each element of the matrix
cm_sum = np.sum(cm, axis=1, keepdims=True)
cm_perc = cm / cm_sum.astype(float) * 100
annot = np.empty_like(cm).astype(str)
nrows, ncols = cm.shape
for i in range(nrows):
    for j in range(ncols):
        c = cm[i, j]
        p = cm_perc[i, j]
        if i == j:
            s = cm_sum[i]
            annot[i, j] = '%.1f%%\n%d/%d' % (p, c, s)
        elif c == 0:
            annot[i, j] = ''
        else:
            annot[i, j] = '%.1f%%\n%d' % (p, c)


# Display confusion matrix 
df_cm = pd.DataFrame(cm, index = matrix_index, columns = matrix_index)
df_cm.index.name = 'Actual'
df_cm.columns.name = 'Predicted'
fig, ax = plt.subplots(figsize=(10,7))
sns.heatmap(df_cm, annot=annot, fmt='')

model.load_weights('model_rev.h5')

from sklearn.metrics import roc_auc_score, classification_report, confusion_matrix
import numpy as np
import seaborn as sns

matrix_index = ['hewan', 'kendaraan', 'percakapan', 'perabotan']

preds = model.predict(X_test)
classpreds = np.argmax(preds, axis=1) # predicted classes 
y_testclass = np.argmax(y_test, axis=1)

cm = confusion_matrix(y_testclass, classpreds)
print(classification_report(y_testclass, classpreds, target_names=matrix_index))

# Get percentage value for each element of the matrix
cm_sum = np.sum(cm, axis=1, keepdims=True)
cm_perc = cm / cm_sum.astype(float) * 100
annot = np.empty_like(cm).astype(str)
nrows, ncols = cm.shape
for i in range(nrows):
    for j in range(ncols):
        c = cm[i, j]
        p = cm_perc[i, j]
        if i == j:
            s = cm_sum[i]
            annot[i, j] = '%.1f%%\n%d/%d' % (p, c, s)
        elif c == 0:
            annot[i, j] = ''
        else:
            annot[i, j] = '%.1f%%\n%d' % (p, c)


# Display confusion matrix 
df_cm = pd.DataFrame(cm, index = matrix_index, columns = matrix_index)
df_cm.index.name = 'Actual'
df_cm.columns.name = 'Predicted'
fig, ax = plt.subplots(figsize=(10,7))
sns.heatmap(df_cm, annot=annot, fmt='')

