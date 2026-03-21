# matches/views.py

from __future__ import annotations

import os

from django.conf import settings
from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from .forms import MatchPlayerDetailFormSet, MatchUploadForm
from .models import Match
from .services import (
    auto_fill_match_result_from_image,
    build_initial_details_from_lobby,
    rollback_match_result,
    save_match_with_details,
    save_temp_uploaded_file,
)
from ratings.models import RatingHistory

LANE_ORDER = {
    "TOP": 0,
    "JGL": 1,
    "MID": 2,
    "ADC": 3,
    "SUP": 4,
}


def _sort_details_by_lane(details):
    return sorted(
        details,
        key=lambda d: (
            LANE_ORDER.get(d.player_selected_lane, 99),
            d.player.player_id,
        ),
    )


def _get_latest_match():
    return Match.objects.order_by("-created_at", "-pk").first()


def _is_latest_match(match):
    latest_match = _get_latest_match()
    return latest_match is not None and latest_match.pk == match.pk


def _get_form_team_value(form):
    value = form["player_team"].value()

    if value in (None, ""):
        initial = form.initial.get("player_team")
        if initial in (None, ""):
            return None
        return int(initial)

    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _split_forms_by_team(detail_formset):
    team1_forms = []
    team2_forms = []
    unknown_forms = []

    for form in detail_formset:
        team_value = _get_form_team_value(form)

        if team_value == 1:
            team1_forms.append(form)
        elif team_value == 2:
            team2_forms.append(form)
        else:
            unknown_forms.append(form)

    for form in unknown_forms:
        if len(team1_forms) < 5:
            team1_forms.append(form)
        else:
            team2_forms.append(form)

    return team1_forms, team2_forms


def _render_upload_page(request, match_form, detail_formset, ocr_text=""):
    team1_forms, team2_forms = _split_forms_by_team(detail_formset)

    return render(
        request,
        "matches/match_upload.html",
        {
            "match_form": match_form,
            "detail_formset": detail_formset,
            "team1_forms": team1_forms,
            "team2_forms": team2_forms,
            "ocr_text": ocr_text,
        },
    )


def match_list_view(request):
    matches = list(Match.objects.prefetch_related("player_details").all())
    latest_match = _get_latest_match()
    latest_match_pk = latest_match.pk if latest_match else None

    return render(
        request,
        "matches/match_list.html",
        {
            "matches": matches,
            "latest_match_pk": latest_match_pk,
        },
    )


def match_upload_view(request):
    lobby_state = request.session.get("lobby_state", {})
    from_lobby = request.GET.get("from_lobby") == "1"

    if request.method == "POST":
        action = request.POST.get("action", "save_match")
        match_form = MatchUploadForm(request.POST, request.FILES)
        detail_formset = MatchPlayerDetailFormSet(request.POST)

        if action == "ocr_autofill":
            if not match_form.is_valid():
                messages.error(request, "경기 기본 정보를 먼저 올바르게 입력해주세요.")
                return _render_upload_page(request, match_form, detail_formset, ocr_text="")

            temp_screenshot_path = match_form.cleaned_data.get("temp_screenshot_path", "")
            uploaded_screenshot = match_form.cleaned_data.get("screenshot")

            if uploaded_screenshot:
                temp_screenshot_path = save_temp_uploaded_file(uploaded_screenshot)
            elif not temp_screenshot_path:
                messages.error(request, "자동 결과 업로드를 하려면 스크린샷을 업로드해야 합니다.")
                return _render_upload_page(request, match_form, detail_formset, ocr_text="")

            absolute_path = os.path.join(settings.MEDIA_ROOT, temp_screenshot_path)

            valid_forms = [form for form in detail_formset if form.is_valid() and form.cleaned_data]

            if len(valid_forms) != 10:
                messages.error(request, "자동 결과 업로드 전에 플레이어 상세 정보 10명이 먼저 채워져 있어야 합니다.")
                keep_form = MatchUploadForm(
                    initial={
                        "match_id": match_form.cleaned_data["match_id"],
                        "win_team": match_form.cleaned_data["win_team"],
                        "temp_screenshot_path": temp_screenshot_path,
                    }
                )
                return _render_upload_page(request, keep_form, detail_formset, ocr_text="")

            initial_details = []
            for form in valid_forms:
                initial_details.append(
                    {
                        "player": form.cleaned_data["player"],
                        "player_team": form.cleaned_data["player_team"],
                        "player_kda": form.cleaned_data.get("player_kda", ""),
                        "player_selected_lane": form.cleaned_data["player_selected_lane"],
                        "player_gold": form.cleaned_data.get("player_gold", ""),
                    }
                )

            mined_rows = auto_fill_match_result_from_image(absolute_path, initial_details)

            new_match_form = MatchUploadForm(
                initial={
                    "match_id": match_form.cleaned_data["match_id"],
                    "win_team": match_form.cleaned_data["win_team"],
                    "temp_screenshot_path": temp_screenshot_path,
                }
            )
            new_detail_formset = MatchPlayerDetailFormSet(initial=mined_rows)

            messages.success(request, "비율 기반 OCR 자동 결과 업로드를 수행했습니다. 값을 확인 후 저장해주세요.")
            return _render_upload_page(
                request,
                new_match_form,
                new_detail_formset,
                ocr_text="row-based OCR completed",
            )

        if match_form.is_valid() and detail_formset.is_valid():
            valid_forms = [form for form in detail_formset if form.cleaned_data]

            if len(valid_forms) != 10:
                messages.error(request, "플레이어 상세 정보는 정확히 10명 입력해야 합니다.")
                return _render_upload_page(request, match_form, detail_formset, ocr_text="")

            team1_count = 0
            team2_count = 0

            for form in valid_forms:
                team_value = int(form.cleaned_data["player_team"])
                if team_value == 1:
                    team1_count += 1
                elif team_value == 2:
                    team2_count += 1

            if team1_count != 5 or team2_count != 5:
                messages.error(request, "팀 1과 팀 2는 각각 정확히 5명이어야 합니다.")
                return _render_upload_page(request, match_form, detail_formset, ocr_text="")

            try:
                match = save_match_with_details(
                    match_form,
                    valid_forms,
                    temp_screenshot_path=match_form.cleaned_data.get("temp_screenshot_path", ""),
                )
                messages.success(request, "경기 결과가 저장되었습니다.")
                return redirect("matches:match_detail", pk=match.pk)
            except ValueError as error:
                messages.error(request, str(error))
                return _render_upload_page(request, match_form, detail_formset, ocr_text="")
            except Exception:
                messages.error(request, "경기 결과 저장 중 오류가 발생했습니다. DB에는 반영되지 않았습니다.")
                return _render_upload_page(request, match_form, detail_formset, ocr_text="")

        return _render_upload_page(request, match_form, detail_formset, ocr_text="")

    if from_lobby:
        initial_rows = build_initial_details_from_lobby(lobby_state)
        detail_formset = MatchPlayerDetailFormSet(initial=initial_rows)
    else:
        detail_formset = MatchPlayerDetailFormSet()

    match_form = MatchUploadForm()

    return _render_upload_page(request, match_form, detail_formset, ocr_text="")


def match_detail_view(request, pk):
    match = get_object_or_404(
        Match.objects.prefetch_related("player_details__player"),
        pk=pk,
    )

    all_details = list(match.player_details.select_related("player").all())

    # 해당 경기의 PS 변동 이력 조회
    histories = RatingHistory.objects.filter(match=match).select_related("player")

    # player_id 기준으로 delta_total 매핑
    delta_map = {
        history.player_id: history.delta_total
        for history in histories
    }

    # 각 detail 객체에 ps_delta 속성 붙이기
    for detail in all_details:
        detail.ps_delta = delta_map.get(detail.player_id, 0)

    team1_details = _sort_details_by_lane(
        [detail for detail in all_details if detail.player_team == 1]
    )
    team2_details = _sort_details_by_lane(
        [detail for detail in all_details if detail.player_team == 2]
    )

    return render(
        request,
        "matches/match_detail.html",
        {
            "match": match,
            "team1_details": team1_details,
            "team2_details": team2_details,
            "is_latest_match": _is_latest_match(match),
        },
    )


@transaction.atomic
def match_delete_view(request, pk):
    match = get_object_or_404(Match, pk=pk)

    if not _is_latest_match(match):
        messages.error(request, "가장 최근 경기만 삭제할 수 있습니다.")
        return redirect("matches:match_detail", pk=match.pk)

    if request.method == "POST":
        rollback_match_result(match)
        match.delete()
        messages.success(request, "경기 결과를 삭제했고, 반영된 승/패 및 PS도 되돌렸습니다.")
        return redirect("matches:match_list")

    return render(
        request,
        "matches/match_confirm_delete.html",
        {
            "match": match,
        },
    )
