# matches/scoreboard_parser.py

from __future__ import annotations

import cv2

from .image_utils import crop_by_ratio
from .ocr_config import HYPERPARAMS
from .ocr_pipeline import ocr_name, ocr_kda, ocr_cs, ocr_gold


def _parse_team_rows(img, team_region: dict, team_number: int):
    """
    팀 영역 1개를 받아 5줄 파싱
    """
    team_img = crop_by_ratio(
        img,
        team_region["x"],
        team_region["y"],
        team_region["w"],
        team_region["h"],
    )

    row_cfg = HYPERPARAMS["row"]
    col_cfg = HYPERPARAMS["columns"]

    rows = []

    for idx in range(row_cfg["count"]):
        row_y = row_cfg["y_offset"] + idx * row_cfg["step"]
        row_h = row_cfg["height"]

        row_img = crop_by_ratio(team_img, 0.0, row_y, 1.0, row_h)

        name_img = crop_by_ratio(row_img, **col_cfg["name"])
        kda_img = crop_by_ratio(row_img, **col_cfg["kda"])
        cs_img = crop_by_ratio(row_img, **col_cfg["cs"])
        gold_img = crop_by_ratio(row_img, **col_cfg["gold"])

        rows.append(
            {
                "team": team_number,
                "row_index": idx,
                "ocr_name": ocr_name(name_img),
                "player_kda": ocr_kda(kda_img),
                "player_cs": ocr_cs(cs_img),
                "player_gold": ocr_gold(gold_img),
            }
        )

    return rows


def parse_scoreboard_image(image_path: str):
    """
    전체 점수표 스크린샷 파싱
    """
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError("이미지를 불러올 수 없습니다.")

    team1_rows = _parse_team_rows(img, HYPERPARAMS["team1"], 1)
    team2_rows = _parse_team_rows(img, HYPERPARAMS["team2"], 2)

    return team1_rows + team2_rows