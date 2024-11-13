import torch.nn as nn
import torch
import torch.nn.functional as F
import cv2
import numpy as np
import math
from scipy.ndimage import uniform_filter
import utils.globals as g

torch.set_num_threads(1)

def draw_tongue_position(rgb_image):
    try:
        face_landmarks_list = g.face_landmarks
        if face_landmarks_list is None:
            return rgb_image

        for idx in range(len(face_landmarks_list)):
            mouth_landmarks = [face_landmarks_list[idx][i] for i in [57, 287, 164, 18]]

            min_x = int(min([lm.x for lm in mouth_landmarks]) * rgb_image.shape[1])
            max_x = int(max([lm.x for lm in mouth_landmarks]) * rgb_image.shape[1])
            min_y = int(min([lm.y for lm in mouth_landmarks]) * rgb_image.shape[0])
            max_y = int(max([lm.y for lm in mouth_landmarks]) * rgb_image.shape[0])

            cv2.rectangle(rgb_image, (min_x, min_y), (max_x, max_y), (255, 0, 0), 2)
            tongue_out = g.data["BlendShapes"][52]["v"]
            if tongue_out >= 0.0001:
                height, width, _ = rgb_image.shape
                left_corner, right_corner = mouth_landmarks[0], mouth_landmarks[1]
                dx = (right_corner.x - left_corner.x) * width
                dy = (right_corner.y - left_corner.y) * height
                angle = math.degrees(math.atan2(dy, dx))

                tongue_x = -g.data["BlendShapes"][62]["v"] * 32
                tongue_y = -g.data["BlendShapes"][63]["v"] * 32

                center = ((min_x + max_x) // 2, (min_y + max_y) // 2)
                M_inv = cv2.getRotationMatrix2D(center, -angle, 1.0)
                tongue_position = np.array([tongue_x + center[0], tongue_y + center[1], 1])
                tongue_original = M_inv.dot(tongue_position)
                tongue_original[0] = np.clip(tongue_original[0], min_x, max_x)
                tongue_original[1] = np.clip(tongue_original[1], min_y, max_y)
                cv2.circle(rgb_image, (int(tongue_original[0]), int(tongue_original[1])), 4, (255, 0, 0), -1)
        return rgb_image
    except Exception as e:
        print(f"Error: {e}")
        return rgb_image

class KeypointCNN(nn.Module):
    def __init__(self, num_keypoints=1):
        super(KeypointCNN, self).__init__()
        self.conv1 = nn.Conv2d(1, 16, kernel_size=3, padding=1)
        self.bn1 = nn.BatchNorm2d(16)
        self.pool = nn.MaxPool2d(2, 2)
        self.conv2 = nn.Conv2d(16, 32, kernel_size=3, padding=1)
        self.bn2 = nn.BatchNorm2d(32)
        self.conv3 = nn.Conv2d(32, 64, kernel_size=3, padding=1)
        self.bn3 = nn.BatchNorm2d(64)
        self.fc1 = nn.Linear(
            64 * 8 * 8, 256
        )  # Adjust the input size according to pooling and input dimensions

        # Keypoint heatmaps output layer: Outputs heatmaps instead of direct coordinates
        # Assuming the output size to be 32x32, which should be adjusted according to your needs
        self.heatmap_conv = nn.Conv2d(64, num_keypoints, kernel_size=3, padding=1)
        self.upsample = nn.Upsample(size=(32, 32), mode="bilinear", align_corners=False)

        self.fc_classifier = nn.Linear(256, 1)  # Classification layer

    def forward(self, x):
        x1 = self.pool(F.relu(self.bn1(self.conv1(x))))
        x2 = self.pool(F.relu(self.bn2(self.conv2(x1))))
        x3 = F.relu(self.bn3(self.conv3(x2)))

        # Keypoint heatmap output
        keypoints_heatmap = self.upsample(self.heatmap_conv(x3))

        x_flat = x3.view(x3.size(0), -1)
        features = F.relu(self.fc1(x_flat))

        classification = torch.sigmoid(self.fc_classifier(features))
        return keypoints_heatmap, classification


def initialize_tongue_model():
    tongue_model = KeypointCNN()
    tongue_model.load_state_dict(
        torch.load("./model/model_epoch_199.pth", weights_only=True)
    )
    tongue_model.eval()
    return tongue_model


def mouth_roi_on_image(rgb_image, face_landmarks):
    try:

        mouth_landmarks = [face_landmarks[i] for i in [57, 287, 164, 18]]

        min_x = min([lm.x for lm in mouth_landmarks])
        max_x = max([lm.x for lm in mouth_landmarks])
        min_y = min([lm.y for lm in mouth_landmarks])
        max_y = max([lm.y for lm in mouth_landmarks])

        height, width, _ = rgb_image.shape
        start_point = (int(min_x * width), int(min_y * height))
        end_point = (int(max_x * width), int(max_y * height))

        left_corner, right_corner = mouth_landmarks[0], mouth_landmarks[1]
        dx = (right_corner.x - left_corner.x) * width
        dy = (right_corner.y - left_corner.y) * height
        angle = math.degrees(math.atan2(dy, dx))

        M = cv2.getRotationMatrix2D(((width // 2), (height // 2)), angle, 1.0)
        rotated_image = cv2.warpAffine(rgb_image, M, (width, height))

        box = np.array(
            [
                [start_point[0], start_point[1]],
                [end_point[0], start_point[1]],
                [end_point[0], end_point[1]],
                [start_point[0], end_point[1]],
            ],
            dtype="float32",
        )
        box_rotated = cv2.transform(np.array([box]), M)[0]

        min_x_rot = max(0, int(min(box_rotated[:, 0])))
        max_x_rot = min(width, int(max(box_rotated[:, 0])))
        min_y_rot = max(0, int(min(box_rotated[:, 1])))
        max_y_rot = min(height, int(max(box_rotated[:, 1])))

        mouth_roi = rotated_image[min_y_rot:max_y_rot, min_x_rot:max_x_rot]
        mouth_roi = cv2.cvtColor(mouth_roi, cv2.COLOR_RGB2GRAY)
        mouth_roi = cv2.resize(mouth_roi, (32, 32), interpolation=cv2.INTER_LINEAR)
        return mouth_roi
    except:
        return None


def max_average_point(heatmap, window_size=5):
    filtered_heatmap = uniform_filter(heatmap, size=window_size)
    best_point = np.unravel_index(np.argmax(filtered_heatmap, axis=None), heatmap.shape)
    return best_point

tongue_count = 0
def detect_tongue(mouth_image, tongue_model, data):
    global tongue_count
    tongue_out, tongue_x, tongue_y = 0.0, 0.0, 0.0
    if mouth_image is not None:
        with torch.no_grad():
            input_tensor = torch.from_numpy(mouth_image).view(1, 1, 32, 32).float()
            input_tensor = input_tensor / 255.0
            out_keypoints, out_classification = tongue_model(input_tensor)
            out_keypoints = out_keypoints * out_classification
            _, _, y, x = max_average_point(out_keypoints.numpy(), 5)
        out_classification_value = out_classification.item()
    else:
        out_classification_value = 0.0

    if out_classification_value > g.config["Tracking"]["Tongue"]["tongue_confidence"]:
        tongue_count += 1
        if tongue_count >= g.config["Tracking"]["Tongue"]["tongue_threshold"]:
            tongue_count = g.config["Tracking"]["Tongue"]["tongue_threshold"]  # Prevent counter from growing too large
            tongue_out = 1.0
            tongue_x = float(-(x / 32 - 0.5) * g.config["Tracking"]["Tongue"]["tongue_x_scalar"])
            tongue_y = float(-(y / 32 - 0.5) * g.config["Tracking"]["Tongue"]["tongue_y_scalar"])
            print(tongue_x, tongue_y, out_classification_value)
    else:
        tongue_count -= 1
        if tongue_count <= 0:
            tongue_count = 0
            tongue_out = 0.0
            tongue_x = 0.0
            tongue_y = 0.0

    # Reset tongue if mouth is closed
    if data["BlendShapes"][25]["v"] < g.config["Tracking"]["Tongue"]["mouth_close_threshold"]:
        tongue_count = 0
        tongue_out = 0.0
        tongue_x = 0.0
        tongue_y = 0.0

    return tongue_out, tongue_x, tongue_y
