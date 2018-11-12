from __future__ import print_function
import argparse
import torch
import torch.utils.data
from torch import nn, optim
from torch.nn import functional as F
from torchvision import datasets, transforms
from torchvision.utils import save_image
from torchvision.datasets import ImageFolder
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms, utils, datasets
from PIL import Image
import sys
from math import exp

from vraec import vraec18

classes = {
    0:"Antiqua",
    1:"Bastarda",
    6:"Rotunda",
    7:"Textura"
}

if len(sys.argv)<3 or len(sys.argv)>4:
    print('Error. Syntax: python3 ocrd_typegroups_classifier.py network-file image-file [stride]')
    quit(1)

print('Loading image...')
sample = Image.open(sys.argv[2])

print('Loading network...')
dev = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
vraec = vraec18(layer_size=96, output_channels=8)
vraec.load_state_dict(torch.load(sys.argv[1], map_location='cpu'))
vraec.to(dev)
for l in range(2, 6):
    vraec.set_variational(l, False)

stride = 96
if len(sys.argv)>3:
    stride = int(sys.argv[3])
print('Using stride', stride)

tensorize = transforms.ToTensor()
batch_size = 64  if torch.cuda.is_available() else 2
nb_classes = 8
score = torch.zeros(1, nb_classes).to(dev)
processed_samples = 0
batch = []
with torch.no_grad():
    for x in range(0, sample.size[0], stride):
        for y in range(0, sample.size[1], stride):
            crop = tensorize(sample.crop((x, y, x+224, y+224)))
            batch.append(crop)
            if len(batch) >= batch_size:
                tensors = torch.stack(batch).to(dev)
                out, _ = vraec(tensors)
                score += out.sum(0)
                processed_samples += len(batch)
                batch = []
    if len(batch) > 0:
        tensors = torch.stack(batch).to(dev)
        out, _ = vraec(tensors)
        score += out.sum(0)
        processed_samples += len(batch)
        batch = []
ssum = 0
for k in classes:
    ssum += score[0,k]

conf = {}
for k in classes:
    conf[score[0,k]] = classes[k]

# Result generation
# TODO: output it correctly, not as a string output to stdio
result='result'
for c in sorted(conf, reverse=True):
    result = '%s:%s=%2.2f' % (result, conf[c], 100 / ssum * c)
print(result)
