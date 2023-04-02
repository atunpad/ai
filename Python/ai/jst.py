import random
import numpy as np


# 1. =====INISIALISASI===============

ni = 4  # Jumlah neuron di input layer
nh = 5  # Jumlah neuron di hidden layer
nout = 3  # Jumlah neuron output layer
lr = 0.9  # nilaai Learning rate
iterasi = 100  # banyaknya iterasi
error_target = 0.01  # Target error

# ---Membersihkan data di Python (Optional)---
# import os
# os.system('clear')  

# ---Menentukan Nilai bobot secara random---
# Bobot antara input ke hidden layer
w = [[random.random() for i in range(ni)] for j in range(nh)]
v = [[random.random() for j in range(nh)] for k in range(nout)]
print(w);
print
print(w[0][2])
print(v);
 
# -- Menentukan nilai target dan masukan --
target = [0.123, 0.456, 0.789]  # target yang ingin dicapai
p = [4, 3, 2, 1]
d = np.zeros(nh)
# -------------------- ITERASI --------------------
#for k in range(iterasi):
    # 2. ------------- FORWARD ------------------------
    # ----- Hidden Layer -----
    # Menghitung d(j) = p(i) * w(j,i) d = sigma p * w
   # for j in range(nh):
   #     htemp = 0  # htemp=h sementara untuk menjumlahkan p*w
   #     for i in range(ni):
   #         htemp = p[i] * w[j][i] + htemp
   #     d[j] = htemp  # d(j) hasil hitung sigma p*w
   #     print(d[1])
# Initialize d and h lists
h = np.zeros(nh)
# Calculate output of hidden layer
for j in range(nh):
    htemp = 0
    for i in range(ni):
        htemp = p[i]*w[j][i] + htemp
    d[j] = htemp
    h[j] = 1 / (1 + np.exp(-d[j]))  # Sigmoid activation function

# Initialize q list
print(d)
print(h)
q = np.zeros(nout)
a = np.zeros(nout)
# Calculate output of output layer
for m in range(nout):
    qtemp = 0
    for j in range(nh):
        qtemp = h[j]*v[m][j] + qtemp
    q[m] = qtemp
    a[m] = 1 / (1 + np.exp(-q[m]))
print(q)
print(a)


