import numpy as np
import matplotlib.pyplot as plt

import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim

import glob
import os
from skimage.io import imread

from torch.utils.data import Dataset


class DataLoader(Dataset):
    def __init__(self, split="stage1_train", path_to_data='/Users/ondra/Dev/Personal/cnn-cells/data-science-bowl-2018'):
        self.split = split
        self.path = path_to_data + '/' + split

        self.id_list = os.listdir(self.path)
        self.image_list = []
        self.mask_list = []

#       set_trace()
        for id in self.id_list:
            images = glob.glob(self.path + '/' + id + '/images/*png')
            masks = glob.glob(self.path + '/' + id + '/masks/*png')
            self.image_list.extend(images)
            self.mask_list.append(masks)

    def __len__(self):
        return len(self.id_list)

    def __getitem__(self, index):
        # zpracovat zde, centroidy
        # set_trace()
        im = imread(self.image_list[index])
        msk = self.combine_masks(self.mask_list[index])
        image = torch.Tensor(im.astype(np.float32))
        mask = torch.Tensor(msk.astype(np.float32))
        return image, mask
    # load and preprocess one image - with number index
    # torchvision.transforms  contains several preprocessing functions for images

    def combine_masks(self, mask_paths):
        comb_mask = None
        for path in mask_paths:
            mask = imread(path)
            if comb_mask is None:
                comb_mask = np.zeros_like(mask)
            comb_mask += mask
        return comb_mask

loader = DataLoader(split='stage1_train')
trainloader = DataLoader(
    loader, batch_size=2, num_workers=0, shuffle=True, drop_last=True)


for it, (batch, masks) in enumerate(trainloader):  # you can iterate over dataset (one epoch)
    print(batch)
    print(batch.size())
    print(masks)
    plt.imshow(batch[0, :, :].detach().cpu().numpy())
    break
