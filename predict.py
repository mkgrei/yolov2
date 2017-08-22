import cv2
import os
import numpy as np
import tensorflow as tf
import keras.backend as K
from models.yolov2 import YOLOv2
from models.predict import predict
from utils.visualize import draw_bboxes
from utils.draw_boxes import DrawingBox
from cfg import *

import argparse

parser = argparse.ArgumentParser("Over-fit model to validate loss function")

parser.add_argument('-p', '--path', help="Path to image file", type=str, default=None)
parser.add_argument('-w', '--weights', help="Path to pre-trained weight files", type=str, default=None)
parser.add_argument('-o', '--output-path', help="Save image to output directory", type=str, default=None)
parser.add_argument('-i', '--iou', help="IoU value for Non-max suppression", type=float, default=0.5)
parser.add_argument('-t', '--threshold', help="Threshold value to display box", type=float, default=0.1)

ANCHORS = np.asarray(ANCHORS).astype(np.float32)

from utils.preprocess_img import preprocess_img


def _main_():
    args = parser.parse_args()

    IMG_PATH = args.path
    WEIGHTS = args.weights
    OUTPUT = args.output_path
    IOU = args.iou
    THRESHOLD = args.threshold

    if not os.path.isfile(IMG_PATH):
        print("Image path is invalid.")
        exit()
    if not os.path.isfile(WEIGHTS):
        print("Weight file is invalid")
        exit()

    # Load class names
    with open(CATEGORIES, mode='r') as txt_file:
        class_names = [c.strip() for c in txt_file.readlines()]

    with tf.Session() as sess:
        yolov2 = YOLOv2(img_size=(IMG_INPUT, IMG_INPUT, 3), num_classes=N_CLASSES, num_anchors=len(ANCHORS))
        yolov2.load_weights(WEIGHTS)

        img_shape = K.placeholder(shape=(2,))

        boxes, classes, scores = \
            predict(yolov2, img_shape, n_classes=N_CLASSES, anchors=ANCHORS, iou_threshold=IOU,
                    score_threshold=THRESHOLD)

        orig_img = cv2.cvtColor(cv2.imread(IMG_PATH), cv2.COLOR_BGR2RGB)
        height, width, _ = orig_img.shape
        img = preprocess_img(cv2.resize(orig_img, (IMG_INPUT, IMG_INPUT)))
        img = np.expand_dims(img, 0)

        pred_bboxes, pred_classes, pred_scores = sess.run([boxes, classes, scores],
                                                          feed_dict={
                                                              yolov2.input: img,
                                                              img_shape: [height, width],
                                                              K.learning_phase(): 0
                                                          })
        bboxes = []
        for box, cls, score in zip(pred_bboxes, pred_classes, pred_scores):
            y1, x1, y2, x2 = box
            bboxes.append(DrawingBox(x1, y1, x2, y2, class_names[cls], score))
            print("Found {} with {}% on image {}".format(class_names[cls], score, IMG_PATH.split('/')[-1]))

        # Save image to evaluation dir
        if OUTPUT is not None:
            result = draw_bboxes(orig_img, bboxes)
            result.save('./evaluation/' + IMG_PATH.split('/')[-1])


if __name__ == "__main__":
    _main_()
    print("Done!")