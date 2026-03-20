HYPERPARAMS = {
    "team1": {"x": 0.020, "y": 0.370, "w": 0.6, "h": 0.246},
    "team2": {"x": 0.020, "y": 0.673, "w": 0.6, "h": 0.246},
    "row": {
        "count": 5,
        "y_offset": 0.00,
        "height": 0.20,
        "step": 0.20,
    },
    "columns": {
        "name": {"x": 0.155, "y": 0.00, "w": 0.205, "h": 1.00},
        "kda":  {"x": 0.650, "y": 0.00, "w": 0.135, "h": 1.00},
        "cs":   {"x": 0.805, "y": 0.00, "w": 0.075, "h": 1.00},
        "gold": {"x": 0.912, "y": 0.00, "w": 0.100, "h": 1.00},
    }
}

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