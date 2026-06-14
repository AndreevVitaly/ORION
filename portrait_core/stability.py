"""Оценка повторяемости признаков по серии фотографий."""

import math
from statistics import fmean, pstdev


STABILITY_SCHEMA_VERSION = 1


def _feature_values(report: dict) -> dict:
    profile = report.get("profile", {})
    return {
        name: feature["value"]
        for name, feature in profile.get("dense_features", {}).items()
        if (
            feature.get("value") is not None
            and feature.get("topology_invariant", True)
        )
    }


def _feature_roles(report: dict) -> dict:
    profile = report.get("profile", {})
    return {
        name: feature.get("role", "morphology")
        for name, feature in profile.get("dense_features", {}).items()
    }


def analyze_report_stability(reports: list[dict]) -> dict:
    """Сравнить численные признаки нескольких отчетов одного человека."""
    if len(reports) < 2:
        raise ValueError("Для оценки стабильности нужны минимум два отчета")

    feature_sets = [_feature_values(report) for report in reports]
    roles = _feature_roles(reports[0])
    common_names = set(feature_sets[0])
    for feature_set in feature_sets[1:]:
        common_names &= feature_set.keys()

    features = {}
    for name in sorted(common_names):
        values = [feature_set[name] for feature_set in feature_sets]
        mean = fmean(values)
        standard_deviation = pstdev(values)
        coefficient_of_variation = (
            standard_deviation / abs(mean)
            if not math.isclose(mean, 0.0)
            else None
        )
        if coefficient_of_variation is None:
            status = "indeterminate"
        elif coefficient_of_variation <= 0.05:
            status = "stable"
        elif coefficient_of_variation <= 0.12:
            status = "moderate"
        else:
            status = "unstable"
        features[name] = {
            "mean": mean,
            "standard_deviation": standard_deviation,
            "coefficient_of_variation": coefficient_of_variation,
            "status": status,
            "sample_count": len(values),
            "role": roles.get(name, "morphology"),
        }

    available = [
        feature["coefficient_of_variation"]
        for feature in features.values()
        if feature["coefficient_of_variation"] is not None
    ]
    mean_cv = fmean(available) if available else None
    role_summaries = {}
    for role in sorted({feature["role"] for feature in features.values()}):
        role_features = [
            feature
            for feature in features.values()
            if feature["role"] == role
        ]
        role_values = [
            feature["coefficient_of_variation"]
            for feature in role_features
            if feature["coefficient_of_variation"] is not None
        ]
        role_summaries[role] = {
            "feature_count": len(role_features),
            "mean_coefficient_of_variation": (
                fmean(role_values) if role_values else None
            ),
            "stable_count": sum(
                feature["status"] == "stable"
                for feature in role_features
            ),
        }

    return {
        "schema_version": STABILITY_SCHEMA_VERSION,
        "sample_count": len(reports),
        "common_feature_count": len(features),
        "mean_coefficient_of_variation": mean_cv,
        "features": features,
        "roles": role_summaries,
    }


def build_series_profile(
    reports: list[dict],
    *,
    subject_label: str | None = None,
) -> dict:
    """Собрать профиль повторяемости полной и качественной подвыборок."""
    if len(reports) < 2:
        raise ValueError("Для профиля серии нужны минимум два отчета")
    passed = [
        report
        for report in reports
        if report.get("quality", {}).get("status") == "passed"
    ]
    strict = [
        report
        for report in passed
        if (
            report.get("profile", {})
            .get("confidence", {})
            .get("components", {})
            .get("pose", 0.0)
            >= 0.6
        )
    ]
    comparison = {"all": analyze_report_stability(reports)}
    if len(passed) >= 2:
        comparison["quality_passed"] = analyze_report_stability(passed)
    if len(strict) >= 2:
        comparison["quality_and_pose"] = analyze_report_stability(strict)

    selected_name = (
        "quality_passed"
        if "quality_passed" in comparison
        else "all"
    )
    selected = comparison[selected_name]
    morphology = {
        name: feature
        for name, feature in selected["features"].items()
        if feature["role"] == "morphology"
    }
    return {
        "schema_version": 1,
        "subject_label": subject_label,
        "sample_count": len(reports),
        "quality_passed_count": len(passed),
        "strict_count": len(strict),
        "selected_group": selected_name,
        "comparison": comparison,
        "stable_morphology": {
            name: feature
            for name, feature in morphology.items()
            if feature["status"] == "stable"
        },
        "moderate_morphology": {
            name: feature
            for name, feature in morphology.items()
            if feature["status"] == "moderate"
        },
        "unstable_morphology": {
            name: feature
            for name, feature in morphology.items()
            if feature["status"] == "unstable"
        },
        "expression": {
            name: feature
            for name, feature in selected["features"].items()
            if feature["role"] == "expression"
        },
        "diagnostic": {
            name: feature
            for name, feature in selected["features"].items()
            if feature["role"] == "diagnostic"
        },
    }
