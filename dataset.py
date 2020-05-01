import os
import glob
import numpy as np
import torch
from PIL import Image, ImageDraw
from skimage import draw
from skimage.io import imread
from matplotlib import pyplot as plt
from scipy.ndimage.filters import gaussian_filter
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms as T

from settings import BASE_DIR
from utils import transforms as my_T

dataset_path = os.path.join(BASE_DIR, 'data-science-bowl-2018')


def get_transform(train=False):
    transforms = []
    if train:
        transforms.append(my_T.Rescale((256, 256)))
    transforms.append(my_T.ToTensor())
    return my_T.Compose(transforms)


class MyDataset(Dataset):
    def __init__(self, transforms=None, split="stage1_train", path=dataset_path):
        self.split = split
        self.path = path + '/' + split

        self.transforms = transforms

        self.path_id_list = glob.glob(os.path.join(self.path, '*'))
        self.id_list = []
        self.image_list = []
        self.mask_list = []

        for path_id in self.path_id_list:
            images = glob.glob(path_id + '/images/*png')
            masks = glob.glob(path_id + '/masks/*png')
            self.id_list.append(os.path.basename(path_id))
            self.image_list.extend(images)
            self.mask_list.append(masks)

    def __len__(self):
        return len(self.path_id_list)

    def __getitem__(self, index):
        image = np.array(Image.open(self.image_list[index]), dtype=np.uint8)
        image = image[:, :, :3]  # remove alpha channel
        boxes, labels = self.mask_to_bbox(self.mask_list[index])
        targets = \
            {
                'boxes': torch.FloatTensor(boxes),
                'labels': torch.LongTensor(labels),
                'name': self.id_list[index]
            }


        if self.transforms is not None:
            image, targets = self.transforms(image, targets)

        return image, targets

    def mask_to_bbox(self, mask_paths):
        boxes = []
        labels = []
        for path in mask_paths:
            mask = Image.open(path)
            mask = np.array(mask)
            pos = np.where(mask)
            xmin = np.min(pos[1])
            xmax = np.max(pos[1])
            ymin = np.min(pos[0])
            ymax = np.max(pos[0])
            if xmin != xmax and ymin != ymax:
                boxes.append([xmin, ymin, xmax, ymax])
                labels.append(1)  # every mask is cell
        return boxes, labels

    def combine_masks(self, mask_paths):
        comb_mask = None
        for path in mask_paths:
            # mask = Image.open(path)
            mask = imread(path)
            count = (mask == 255).sum()
            y, x = np.argwhere(mask == 255).sum(0) / count
            if comb_mask is None:
                # comb_mask = np.zeros_like(mask)
                comb_mask = np.zeros_like(mask)
            # comb_mask += mask
            rr, cc = draw.circle(y, x, radius=3)
            try:
                comb_mask[rr, cc] = 255
            except IndexError:
                pass
            blurred = gaussian_filter(comb_mask, sigma=1)
        # fig = plt.figure()
        # fig.add_subplot(1, 2, 1)
        # plt.imshow(comb_mask,cmap="gray")
        # fig.add_subplot(1, 2, 2)
        # plt.imshow(comb_mask,cmap="gray")
        # plt.show(block=True)

        return Image.fromarray(blurred)


if __name__ == "__main__":

    # def my_collate(batch):
    #     image = batch[0]
    #     target = [item[1] for item in batch]
    #     return image, target

    def my_collate(batch):
        data = [item[0] for item in batch]
        target = [item[1] for item in batch]
        return data, target

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Running on {device}")

    dataset = MyDataset(split='stage1_train', transforms=get_transform(train=True))
    trainloader = DataLoader(dataset, batch_size=1, num_workers=0, shuffle=True, collate_fn=my_collate)
    it = iter(trainloader)
    image, targets = next(it)
    print(image)
    print(targets)
    print("-----")
    image, targets = dataset[1]
    name = targets["name"]
    # image = image[None, :, :, :]
    image = image.to(device=device)
    targets = [{
        "boxes": targets["boxes"].to(device=device),
        "labels": targets["labels"].to(device=device),
        "name": targets["name"]
    }]
    print(image)
    print(targets)

    image = Image.fromarray(image.numpy()[0, 0, :, :])
    if image.mode != "RGB":
        image = image.convert("RGB")
    draw = ImageDraw.Draw(image)
    for box in targets[0]["boxes"]:
        x0, y0, x1, y1 = box
        draw.rectangle([(x0, y0), (x1, y1)], outline=(255, 0, 255))

    image.show(title=name)
