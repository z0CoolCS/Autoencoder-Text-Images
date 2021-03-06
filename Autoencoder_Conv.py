# -*- coding: utf-8 -*-
"""Proyecto6_Conv.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1r6OMzo9zZ-EJjRMnP7rTQ9Nd-lOY9dKj

## ***Clean GPU***
"""

import gc
gc.collect()
torch.cuda.empty_cache()

"""## ***Packages***"""

import torch
import torch.nn as nn 
import torch.optim as optim 
from torchvision import datasets 
from torchvision import transforms
from torch.utils.data import Subset, DataLoader
from torch.utils.data import Dataset # to custom class dataset
from torchvision.io import read_image # ?
import torch.nn.functional as F

import matplotlib.pyplot as plt
import numpy as np
import os
import cv2
from PIL import Image
import random
import datetime
from sklearn.model_selection import StratifiedShuffleSplit
from sklearn.model_selection import train_test_split
from sklearn.model_selection import KFold

device = (torch.device('cuda') if torch.cuda.is_available() else torch.device('cpu'))
print(f"Training on device {device}.")

"""## ***Build Dataset***"""

my_transform = transforms.Compose([
                                   transforms.Resize((256, 256)),
                                   transforms.ToTensor()
                                  ])

path_image_cleaned = "/content/drive/MyDrive/Colab Notebooks/UTEC - IA/data/project6/train_cleaned"
path_image_train = "/content/drive/MyDrive/Colab Notebooks/UTEC - IA/data/project6/train"
path_image_test = "/content/drive/MyDrive/Colab Notebooks/UTEC - IA/data/project6/test"
path_models = "/content/drive/MyDrive/Colab Notebooks/UTEC - IA/models/"

img = read_image(path_image_cleaned+"/2.png")
plt.imshow(img.squeeze())

def load_images_from_folder(folder, my_transform):
    data = []
    for f in sorted(os.listdir(folder + '/')):
        img = Image.open(folder + '/' + f)
        img = my_transform(img)
        img = img.squeeze()
        data.append(img.type(torch.float32))
    return data

data_cleaned = load_images_from_folder(path_image_cleaned, my_transform)
data_train = load_images_from_folder(path_image_train, my_transform)
data_test = load_images_from_folder(path_image_test, my_transform)

X_train, X_test, y_train, y_test = train_test_split(data_train, data_cleaned, test_size=0.30, random_state=42)

tensor_cleaned_t = torch.stack(y_train)
tensor_train_t = torch.stack(X_train)
tensor_cleaned_val = torch.stack(y_test)
tensor_train_val = torch.stack(X_test)
#tensor_cleaned = torch.stack(data_cleaned)
#tensor_train = torch.stack(data_train)
tensor_test = torch.stack(data_test)

data_cleaned[0].shape

def check_size(data_file):
  minx, miny, maxx, maxy = 1000, 1000, 0, 0
  for img in data_file:
    minx = min(minx, img.shape[0])
    miny = min(miny, img.shape[1])
    maxx = max(maxx, img.shape[0])
    maxy = max(maxy, img.shape[1])
  print(minx,miny,maxx,maxy)

index= np.arange(0,tensor_train_t.shape[0])
torch_index = torch.from_numpy(index)
torch_index
#tensor_train.shape

#train_loader = DataLoader(data_train, shuffle=False, batch_size= 4)
#cleaned_loader = DataLoader(data_cleaned, shuffle=False, batch_size= 4)
index_loader = DataLoader(torch_index, shuffle=True, batch_size= 4)

plt.imshow(data_cleaned[0])

"""## ***Training & Validate Function Convolution***"""

def training_loop_conv(n_epochs, optimizer, model, loss_fn, index_loader, t_train, t_cleaned, t_val_x, t_val_y, t_test, k_value = 2):
  errors = []
  validation = []
  tran1_tmp = transforms.ToPILImage()
  for epoch in range(1, n_epochs + 1):
    loss_train = 0.0
    
    for ind in index_loader:
      
      imgs = t_train[ind]
      img_out = imgs[0]
      imgs = imgs.view(imgs.shape[0],1,imgs.shape[1], imgs.shape[2]).to(device)
      
      out = t_cleaned[ind]
      out = out.view(out.shape[0],1,out.shape[1], out.shape[2]).to(device)

      outputs = model(imgs)
      #print(outputs.shape)
      #print(imgs.shape)
      loss = loss_fn(outputs, out)

      optimizer.zero_grad()
      loss.backward()
      optimizer.step()

      loss_train += loss.item()

    if epoch == 1 or epoch % 10 == 0:
      print('{} Epoch {}, Training loss {}'.format( datetime.datetime.now(), epoch, 
                                                   loss_train / (t_train.shape[0])))  
      errors.append(loss_train / (t_train.shape[0]))
      out_conv = outputs[0]
      #print(out_conv.shape)
      out_conv = out_conv.view(out_conv.shape[1], out_conv.shape[2]).to("cpu")
      
      #val_k = validate_conv(model, t_val_x, t_val_y, k_value)
      #validation.append(val_k)
      display(tran1_tmp(img_out))
      display(tran1_tmp(out_conv))
  return errors, validation

def validate_conv(model, train, test, k_value):
  
  error1 = 0
  cont = 0
  with torch.no_grad():
    for img_conv, val_img in zip(train, test):
      img_conv = img_conv.view(1,1,img_conv.shape[0], img_conv.shape[1]).to(device)
      val_img = val_img.view(1,1,val_img.shape[0], val_img.shape[1]).to(device)
      out_conv = model(img_conv)
      error1 += torch.sqrt(torch.sum(torch.pow(val_img - out_conv, 2)))
      cont += 1
  
  print("Validation error  k = {}: {:.2f}".format(k_value, error1 * 1.0 / cont))
  return error1 * 1.0 / cont

"""## ***Model Convolution***"""

class AutoencoderConv(nn.Module):
    def __init__(self):
        super(AutoencoderConv, self).__init__()
          
        self.enc_layer1 = nn.Conv2d(1, 64, 3, padding=1)  
        self.enc_layer2 = nn.Conv2d(64, 32, 3, padding=1)
        self.enc_layer3 = nn.Conv2d(32, 16, 3, padding=1)

        self.batch1 = nn.BatchNorm2d(64)
        self.batch2 = nn.BatchNorm2d(32)
        self.batch3 = nn.BatchNorm2d(16)

        
        self.pool = nn.MaxPool2d(2, 2)
        self.out_conv = nn.Conv2d(128, 1, kernel_size=3, padding=1)
        
        self.dec_layer1 = nn.ConvTranspose2d(16, 32, 2, stride=2)
        self.dec_layer2 = nn.ConvTranspose2d(32, 64, 2, stride=2)
        self.dec_layer3 = nn.ConvTranspose2d(64, 128, 2, stride=2)
        

    def forward(self, out):
        
        out = self.batch1(F.relu(self.enc_layer1(out)))
        out = self.pool(out)
        out = self.batch2(F.relu(self.enc_layer2(out)))
        out = self.pool(out)
        out = self.batch3(F.relu(self.enc_layer3(out)))
        out = self.pool(out)


        out = self.batch2(F.relu(self.dec_layer1(out)))
        out = self.batch1(F.relu(self.dec_layer2(out)))
        out = F.relu(self.dec_layer3(out))
        out = self.out_conv(out)
        out = torch.sigmoid(out)

        return out

class AutoencoderConv3(nn.Module):
    def __init__(self):
        super(AutoencoderConv3, self).__init__()
          
        self.enc_layer1 = nn.Conv2d(1, 128, 3, padding=1)  
        self.enc_layer2 = nn.Conv2d(128, 64, 3, padding=1)
        self.enc_layer3 = nn.Conv2d(64, 32, 3, padding=1)

        self.batch1 = nn.BatchNorm2d(128)
        self.batch2 = nn.BatchNorm2d(64)
        self.batch3 = nn.BatchNorm2d(32)

        
        self.pool = nn.MaxPool2d(2, 2)
        self.out_conv = nn.Conv2d(256, 1, kernel_size=3, padding=1)
        
        self.dec_layer1 = nn.ConvTranspose2d(32, 64, 2, stride=2)
        self.dec_layer2 = nn.ConvTranspose2d(64, 128, 2, stride=2)
        self.dec_layer3 = nn.ConvTranspose2d(128, 256, 2, stride=2)
        

    def forward(self, out):
        
        out = self.batch1(F.relu(self.enc_layer1(out)))
        out = self.pool(out)
        out = self.batch2(F.relu(self.enc_layer2(out)))
        out = self.pool(out)
        out = self.batch3(F.relu(self.enc_layer3(out)))
        out = self.pool(out)


        out = self.batch2(F.relu(self.dec_layer1(out)))
        out = self.batch1(F.relu(self.dec_layer2(out)))
        out = F.relu(self.dec_layer3(out))
        out = self.out_conv(out)
        out = torch.sigmoid(out)

        return out

"""## ***Training Model Convolutional***"""

model_conv = AutoencoderConv2().to(device)
optimizer_conv = optim.Adam(model_conv.parameters(), lr=1e-3)
loss_fn_conv = nn.MSELoss()

torch.save(model_conv.state_dict(), path_models + "cnn1.pt")

#model
weights = sum(p.numel() for p in model_conv.parameters())
weights/10**6

model_conv

errors_conv, accuracies_conv = training_loop_conv( 
    n_epochs = 200,
    optimizer = optimizer_conv,
    model = model_conv,
    loss_fn = loss_fn_conv,
    index_loader = index_loader,
    t_train = tensor_train_t,
    t_cleaned = tensor_cleaned_t,
    t_val_x = tensor_train_val,
    t_val_y = tensor_cleaned_val,
    t_test = tensor_test
    )

tran1_tmp = transforms.ToPILImage()
for img_conv in data_test:
  display(tran1_tmp(img_conv))
  img_conv = img_conv.view(1,1,img_conv.shape[0], img_conv.shape[1]).to(device)
  out_conv = model_conv(img_conv)
  out_conv = out_conv.view(out_conv.shape[2], out_conv.shape[3]).to("cpu")
  display(tran1_tmp(out_conv))

img_conv = data_cleaned[10]
plt.imshow(img_conv)
plt.show()
img_conv = img_conv.view(1,1,img_conv.shape[0], img_conv.shape[1]).to(device)

out_conv = model_conv(img_conv)
#out = out.view(420,540).to("cpu")
out_conv.shape

#img = img.to("cpu")
out_conv = out_conv.view(out_conv.shape[2], out_conv.shape[3]).to("cpu")
out_conv = out_conv.detach().numpy()
plt.imshow(out_conv)

