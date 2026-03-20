# ocr_pipeline_debug.py

from __future__ import annotations

import re
from typing import Optional

import cv2
import numpy as np
import pytesseract


# -----------------------------
# OCR 설정값
# -----------------------------
OCR_CONFIG_NAME = "--psm 7 -l kor+eng"
OCR_CONFIG_KDA = "--psm 7 -c tessedit_char_whitelist=0123456789/"
OCR_CONFIG_CS = "--psm 7 -c tessedit_char_whitelist=0123456789"
OCR_CONFIG_GOLD = "--psm 7 -c tessedit_char_whitelist=0123456789,"

NAME_PREPROCESS = {
    "scale": 2.5,
    "threshold": 145,
    "bilateral_d": 9,
    "bilateral_sigma_color": 75,
    "bilateral_sigma_space": 75,
}

NUM_PREPROCESS = {
    "scale": 2.0,
    "threshold": 150,
    "gaussian_kernel": (5, 5),
}


# -----------------------------
# 전처리 함수
# -----------------------------
def preprocess_for_name(img):
    """
    한글/영문 이름 OCR용 전처리
    - 회색/노란 글씨 간극을 줄이기 위한 버전
    """
    # 1. 확대
    img = cv2.resize(
        img,
        None,
        fx=3.0,
        fy=3.0,
        interpolation=cv2.INTER_CUBIC,
    )

    # 2. LAB 색공간으로 변환 후 밝기 채널 사용
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l_channel, a_channel, b_channel = cv2.split(lab)

    # 3. CLAHE로 국소 대비 향상
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    l_channel = clahe.apply(l_channel)

    # 4. 노이즈를 줄이되 글자 획은 유지
    filtered = cv2.bilateralFilter(l_channel, 9, 75, 75)

    # 5. Otsu threshold
    _, thresh = cv2.threshold(
        filtered,
        0,
        255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )

    # 6. 획 보정
    kernel = np.ones((2, 2), np.uint8)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

    return thresh

def preprocess_for_number(img: np.ndarray) -> np.ndarray:
    """
    숫자 OCR용 전처리
    """
    img = cv2.resize(
        img,
        None,
        fx=NUM_PREPROCESS["scale"],
        fy=NUM_PREPROCESS["scale"],
        interpolation=cv2.INTER_CUBIC,
    )

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, NUM_PREPROCESS["gaussian_kernel"], 0)

    _, thresh = cv2.threshold(
        gray,
        NUM_PREPROCESS["threshold"],
        255,
        cv2.THRESH_BINARY,
    )

    return thresh


# -----------------------------
# OCR 함수
# -----------------------------
def ocr_name(img: np.ndarray) -> str:
    """
    이름 OCR
    """
    processed = preprocess_for_name(img)
    text = pytesseract.image_to_string(processed, config=OCR_CONFIG_NAME)

    text = text.strip()
    text = re.sub(r"\s+", "", text)

    return text


def ocr_kda(img: np.ndarray) -> str:
    """
    KDA OCR
    """
    processed = preprocess_for_number(img)
    text = pytesseract.image_to_string(processed, config=OCR_CONFIG_KDA)

    match = re.search(r"\d+\s*/\s*\d+\s*/\s*\d+", text)
    if not match:
        return ""

    return re.sub(r"\s+", "", match.group())


def ocr_cs(img: np.ndarray) -> Optional[int]:
    """
    CS OCR
    """
    processed = preprocess_for_number(img)
    text = pytesseract.image_to_string(processed, config=OCR_CONFIG_CS)

    match = re.search(r"\d{1,3}", text)
    if not match:
        return None

    return int(match.group())


def ocr_gold(img: np.ndarray) -> Optional[int]:
    """
    골드 OCR
    """
    processed = preprocess_for_number(img)
    text = pytesseract.image_to_string(processed, config=OCR_CONFIG_GOLD)

    text = text.replace(",", "")
    match = re.search(r"\d{4,5}", text)
    if not match:
        return None

    return int(match.group())