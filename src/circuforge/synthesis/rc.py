from circuforge.domain.specs import CircuitCandidate, DesignSpec


def netlist(spec: DesignSpec, candidate: CircuitCandidate) -> str:
    """Only typed numeric values enter this fixed batch-mode template."""
    spec.validate_candidate(candidate)
    sweep = spec.sweep
    elements = (
        f"R1 in out {candidate.resistance_ohm:.17g}\nC1 out 0 {candidate.capacitance_f:.17g}\n"
        if candidate.topology == "rc_lowpass" else
        f"C1 in out {candidate.capacitance_f:.17g}\nR1 out 0 {candidate.resistance_ohm:.17g}\n"
    )
    return (
        f"CircuForge ideal unloaded {candidate.topology}\n"
        f"V1 in 0 AC {spec.source_amplitude_v:.17g}\n"
        + elements +
        ".options numdgt=15 width=200\n"
        f".ac dec {sweep.points_per_decade} {sweep.start_hz:.17g} {sweep.stop_hz:.17g}\n"
        ".print ac vr(out) vi(out)\n"
        ".end\n"
    )
