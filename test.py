import argparse
import os
import re
import cv2
import numpy as np
from utils.draw_boxes import draw

import tensorflow as tf
import keras.backend as K

from keras.layers import Input
from keras.models import Model

from models.yolov2_darknet import yolov2_darknet
from cfg import ANCHORS, IMG_INPUT_SIZE, N_CLASSES, CATEGORIES


def _main_(parser):

    # ###############
    # Parse Config  #
    # ###############
    args = parser.parse_args()
    img_path         = args.path
    weight_file      = args.weights
    output_dir       = args.output_path
    iou              = args.iou
    scores_threshold = args.threshold
    anchors, label_dict = config_prediction()

    with tf.Session() as sess:

        inputs                 = Input(shape=(None, None, 3), name='image_input')
        # ###################
        # Define Keras Model
        # ###################
        outputs = yolov2_darknet(is_training = False,
                                 inputs      = inputs,
                                 img_size    = IMG_INPUT_SIZE,
                                 anchors     = anchors,
                                 num_classes = N_CLASSES,
                                 iou         = iou,
                                 scores_threshold = scores_threshold)

        model = Model(inputs=inputs, outputs=outputs)
        model.load_weights(weight_file)
        model.summary()
        # ######################################
        # Run a session to make one prediction #
        # ######################################
        image = cv2.imread(img_path)
        pred_bboxes, pred_classes, pred_scores = sess.run(outputs,
                                                          feed_dict={
                                                              K.learning_phase(): 0,
                                                              inputs: np.expand_dims(image, axis=0),
                                                          })

        # #################
        # Display Result  #
        # #################
        pred_classes = [label_dict[idx] for idx in pred_classes]

        h, w, _ = image.shape
        if output_dir is not None:
            result = draw(image, pred_bboxes, pred_classes, pred_scores)
            cv2.imwrite(os.path.join(output_dir, img_path.split('/')[-1].split('.')[0] + '_result.jpg'), result)


def config_prediction():
    # Config Anchors
    anchors = []
    with open(ANCHORS, 'r') as f:
        data = f.read().splitlines()
        for line in data:
            numbers = re.findall('\d+.\d+', line)
            anchors.append((float(numbers[0]), float(numbers[1])))

    # Load class names
    with open(CATEGORIES, mode='r') as txt_file:
        class_names = [c.strip() for c in txt_file.readlines()]

    label_dict = {v: k for v, k in enumerate(class_names)}
    return np.array(anchors), label_dict


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Over-fit model to validate loss function")

    parser.add_argument('-p', '--path',
                        help="Path to image file", type=str, default='./assets/example.jpg')

    parser.add_argument('-w', '--weights',
                        help="Path to pre-trained weight files", type=str, default='./assets/coco_yolov2.weights')

    parser.add_argument('-o', '--output-path',
                        help="Save image to output directory", type=str, default=None)

    parser.add_argument('-i', '--iou',
                        help="IoU value for Non-max suppression", type=float, default=0.5)

    parser.add_argument('-t', '--threshold',
                        help="Threshold value to display box", type=float, default=0.6)
    _main_(parser)
    print("Done!")