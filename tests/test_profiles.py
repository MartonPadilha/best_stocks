from copy import deepcopy

import pytest

from src.config import Config
from src.profiles import (
    PROFILES, list_profiles, profile_description, build_config,
    validate_config, weights_total, AnalysisConfig,
)


def test_all_profiles_present():
    assert set(list_profiles()) == {"Conservador", "Equilibrado", "Crescimento", "Dividendos/Value"}


def test_profile_description_exists():
    for name in list_profiles():
        assert profile_description(name)


def test_profiles_sum_to_one():
    for name in list_profiles():
        total = weights_total(PROFILES[name]["weights"])
        assert abs(total - 1.0) < 1e-6, f"{name} soma {total}"


def test_build_config_does_not_mutate_config():
    original = deepcopy(Config.WEIGHTS_STOCKS)
    original_caps = deepcopy(Config.INDICATOR_CAPS)
    original_mom = Config.MOMENTUM_WEIGHT

    for name in list_profiles():
        cfg = build_config(name)
        assert cfg.profile_name == name

    assert Config.WEIGHTS_STOCKS == original
    assert Config.INDICATOR_CAPS == original_caps
    assert Config.MOMENTUM_WEIGHT == original_mom


def test_build_config_weights_are_independent_copies():
    cfg1 = build_config("Equilibrado")
    cfg1.weights["roe"]["weight"] = 0.99
    cfg2 = build_config("Equilibrado")
    assert cfg2.weights["roe"]["weight"] != 0.99
    assert PROFILES["Equilibrado"]["weights"]["roe"]["weight"] != 0.99


def test_equilibrado_matches_default_weights():
    cfg = build_config("Equilibrado")
    for ind, meta in Config.WEIGHTS_STOCKS.items():
        assert cfg.weights[ind]["weight"] == pytest.approx(meta["weight"])
        assert cfg.weights[ind]["normalization"] == meta["normalization"]
    assert cfg.momentum_weight == pytest.approx(Config.MOMENTUM_WEIGHT)


def test_invalid_profile_rejected():
    with pytest.raises(ValueError):
        build_config("Inexistente")


def test_negative_weight_rejected():
    weights = deepcopy(PROFILES["Equilibrado"]["weights"])
    weights["roe"]["weight"] = -0.1
    with pytest.raises(ValueError):
        build_config("Equilibrado", weights_override=weights)


def test_sum_not_one_rejected():
    weights = deepcopy(PROFILES["Equilibrado"]["weights"])
    weights["roe"]["weight"] = 0.0
    with pytest.raises(ValueError):
        build_config("Equilibrado", weights_override=weights)


def test_invalid_windows_rejected():
    with pytest.raises(ValueError):
        build_config("Equilibrado", temporal_windows=[90, 30, 180])
    with pytest.raises(ValueError):
        build_config("Equilibrado", temporal_windows=[30, 30, 180])


def test_invalid_winsor_rejected():
    with pytest.raises(ValueError):
        build_config("Equilibrado", winsor_limits=(0.5, 0.4))
    with pytest.raises(ValueError):
        build_config("Equilibrado", winsor_limits=(-0.1, 0.99))


def test_momentum_override():
    cfg = build_config("Equilibrado", momentum_override=0.0)
    assert cfg.momentum_weight == 0.0
    cfg2 = build_config("Equilibrado", momentum_override=0.5)
    assert cfg2.momentum_weight == 0.5


def test_caps_override():
    cfg = build_config("Equilibrado", caps_override={"dy": 99.0})
    assert cfg.indicator_caps["dy"] == 99.0


def test_two_profiles_independent():
    cfg_cons = build_config("Conservador")
    cfg_growth = build_config("Crescimento")
    assert cfg_cons.weights != cfg_growth.weights
    assert cfg_cons.profile_name != cfg_growth.profile_name


def test_conservador_no_momentum():
    cfg = build_config("Conservador")
    assert cfg.momentum_weight == 0.0


def test_validate_config_directly():
    cfg = build_config("Equilibrado")
    validate_config(cfg)
