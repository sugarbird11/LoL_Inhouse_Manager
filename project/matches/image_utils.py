from __future__ import annotations

import cv2


def crop_by_ratio(img, x: float, y: float, w: float, h: float):
    """
    전체 이미지 또는 부분 이미지에서 비율 기준으로 crop
    """
    height, width = img.shape[:2]

    x1 = max(0, int(width * x))
    y1 = max(0, int(height * y))
    x2 = min(width, int(width * (x + w)))
    y2 = min(height, int(height * (y + h)))

    return img[y1:y2, x1:x2]


def draw_ratio_box(img, x: float, y: float, w: float, h: float, color=(0, 255, 0), thickness=2):
    """
    디버그용 박스 그리기
    """
    height, width = img.shape[:2]

    x1 = max(0, int(width * x))
    y1 = max(0, int(height * y))
    x2 = min(width, int(width * (x + w)))
    y2 = min(height, int(height * (y + h)))

    output = img.copy()
    cv2.rectangle(output, (x1, y1), (x2, y2), color, thickness)
    return output