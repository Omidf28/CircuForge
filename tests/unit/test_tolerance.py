"""Sampling/quantile fixtures are mathematical unit data, not simulator evidence."""
import json
import copy
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
from pydantic import ValidationError

from circuforge.domain.specs import CircuitCandidate
from circuforge.domain.tolerance import SamplingPlan, ToleranceModel, perturb, sample_factors
from circuforge.evaluation.statistics import empirical_statistics
from circuforge.optimization.base import Evaluation
from circuforge.optimization.robustness import Experiment, load_experiment, run_trial
from circuforge.simulation.ngspice import SimulationError

MANIFEST = Path(__file__).resolve().parents[2] / "examples/robustness-v1.json"


def test_independent_streams_replay_and_respect_declared_component_envelopes():
    model = ToleranceModel()
    plan = SamplingPlan(seed=42, samples=128, stream="training")
    a = sample_factors(model, plan)
    assert np.array_equal(a, sample_factors(model, plan))
    assert not np.array_equal(a, sample_factors(model, SamplingPlan(seed=42, samples=128, stream="holdout")))
    assert np.all((a >= [0.99, .95]) & (a <= [1.01, 1.05]))
    assert not np.array_equal(a[:, 0], a[:, 1])


def test_zero_tolerances_reduce_exactly_to_nominal_values():
    model = ToleranceModel(resistance_fraction=0., capacitance_fraction=0.)
    factors = sample_factors(model, SamplingPlan(seed=7, samples=4, stream="holdout"))
    candidate = CircuitCandidate()
    assert np.array_equal(factors, np.ones((4, 2)))
    assert all(perturb(candidate, f) == candidate for f in factors)


@pytest.mark.parametrize("bad", [-.01, .21, float("nan"), True])
def test_invalid_tolerance_is_rejected(bad):
    with pytest.raises(ValidationError):
        ToleranceModel(resistance_fraction=bad)


@pytest.mark.parametrize("bad", [True, -1, 2**32])
def test_invalid_sampling_seed_is_rejected(bad):
    with pytest.raises(ValidationError):
        SamplingPlan(seed=bad, samples=8, stream="training")


def test_empirical_quantiles_and_failed_sample_policy():
    values = [Evaluation(candidate=CircuitCandidate(), status="evaluated", constraints_satisfied=True, verified=True,
                         measured_cutoff_hz=x, relative_error=x / 100, objective=x / 10, target_passed=i % 2 == 0)
              for i, x in enumerate([1., 2., 4., 8.])]
    stats = empirical_statistics(values)
    assert stats["pass_rate"] == .5 and stats["samples"] == 4
    assert stats["cutoff_hz"] == pytest.approx({"q05": 1.15, "q50": 3., "q95": 7.4})
    assert stats["relative_error"]["q95"] == pytest.approx(.074)
    with pytest.raises(ValueError, match="failures"):
        empirical_statistics([*values, values[0].model_copy(update={"verified": False})])


@pytest.mark.parametrize("damage", ["cap", "block", "zero", "fixed", "sweep", "physical", "seed", "correlation", "duplicate"])
def test_unsafe_or_ambiguous_experiment_is_rejected(damage):
    data = json.loads(MANIFEST.read_text())
    if damage == "cap":
        data["max_spice_calls"] = 1
    elif damage == "block":
        data["training_calls"] = 65
    elif damage == "zero":
        data["tolerance"].update(resistance_fraction=0., capacitance_fraction=0.)
    elif damage == "fixed":
        s = data["cases"][0]["spec"]
        s["resistance_ohm"] = {"minimum": 1000., "maximum": 1000.}
        s["capacitance_f"] = {"minimum": 1.59e-7, "maximum": 1.59e-7}
    elif damage == "sweep":
        data["cases"][0]["spec"]["sweep"]["start_hz"] = 900.
    elif damage == "physical":
        s = data["cases"][0]["spec"]
        s["resistance_ohm"] = {"minimum": 1e-3, "maximum": 1100.}
    elif damage == "seed":
        data["seeds"] = [7, 7]
    elif damage == "duplicate":
        repeated = copy.deepcopy(data["cases"][0])
        repeated["id"] = "renamed-copy"
        data["cases"].append(repeated)
    else:
        data["tolerance"]["distribution"] = "correlated_gaussian"
    with pytest.raises(ValidationError):
        Experiment.model_validate(data)


def test_config_accounts_for_every_training_and_holdout_call():
    config = load_experiment(MANIFEST)
    assert config.calls_per_trial == 96 and config.configured_calls == 768
    for case in config.cases:
        simulation = config.simulation_spec(case.spec)
        assert simulation.resistance_ohm.minimum < case.spec.resistance_ohm.minimum
        assert simulation.capacitance_f.maximum > case.spec.capacitance_f.maximum
        assert simulation.relative_error_tolerance == case.spec.relative_error_tolerance == .001


def test_all_failed_training_calls_are_preserved_and_never_create_statistics(tmp_path):
    data = json.loads(MANIFEST.read_text())
    data.update(training_calls=8, training_samples=3, holdout_samples=8)
    for case in data["cases"]:
        case["spec"]["max_evaluations"] = 8
    config = Experiment.model_validate(data)

    class FailingSimulator:
        info = SimpleNamespace(version="controlled failure fixture", executable="unavailable-test-fixture")

        def simulate(self, spec, candidate):
            raise SimulationError("launch_error", "controlled failure without substituted output")

    report = run_trial(config, config.cases[0], 7, "robust", FailingSimulator(), tmp_path / "trial")
    assert report["stage"] == "blocked" and report["simulator_calls"] == report["failures"] == 8
    assert report["selected_group"] is report["holdout_statistics"] is None
    assert not report["holdout_calls"]
    assert all(g["objective"] is None for g in report["training_groups"])
    assert (tmp_path / "trial/evaluations/call-0008/evaluation.json").exists()
