#!/usr/bin/env python3
"""End-to-end scenario across the Overby repos, with every packet checked
against the real schemas.

    registry entry (space-reclamation)
      -> OTF-1 capture assignment to a reclaimer
      -> reclaimer position fixed by ranging (satnav-swarm) -> OTF-1 status
      -> OTF-1 capture event handed to a depot (outpost-core)
      -> depot + registry agree on the feedstock totals
      -> two equal-priority vehicles contend for a port
         -> Tier 1 advisory request (validated by ai-roundtable's ADV-1 rules)
         -> ai-roundtable's Jac engine answers it with a recommendation
            (scripted models; this step is skipped if jaclang/byllm are missing)

Expects sibling checkouts under --workspace (default: the folder holding this
repo): outpost-core, satnav-swarm, space-reclamation, ai-roundtable,
telemetry-protocol. Needs `pip install jsonschema`; for the last step also
`pip install -r ai-roundtable/jac/requirements.txt`.

    python integration/run_scenario.py [--workspace DIR] [--quiet]
"""
import argparse
import json
import math
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPOS = ["outpost-core", "satnav-swarm", "space-reclamation", "ai-roundtable", "telemetry-protocol"]


def load_modules(workspace: Path):
    missing = [r for r in REPOS if not (workspace / r).is_dir()]
    if missing:
        raise SystemExit(f"missing sibling checkouts under {workspace}: {', '.join(missing)}")
    for r in ("outpost-core", "satnav-swarm"):
        sys.path.insert(0, str(workspace / r))
    for r in ("space-reclamation/tools", "ai-roundtable/tools"):
        sys.path.insert(0, str(workspace / r))
    import jsonschema
    import otf1_bridge
    import outpost_core
    import satnav_swarm
    import validate as adv_validate
    schema = json.loads((workspace / "telemetry-protocol/schema/otf-1.schema.json").read_text(encoding="utf-8"))
    return jsonschema, otf1_bridge, outpost_core, satnav_swarm, adv_validate, schema


def run(workspace: Path, log=print) -> dict:
    jsonschema, bridge, outpost, satnav, adv, otf1 = load_modules(workspace)
    otf1_validator = jsonschema.Draft202012Validator(otf1)
    checked = []

    def ok(name, pkt):
        errs = list(otf1_validator.iter_errors(pkt))
        assert not errs, f"{name} is not valid OTF-1: {errs[0].message}"
        checked.append(name)
        log(f"  valid OTF-1 {pkt.get('kind', 'event'):<10} {name}")
        return pkt

    now = datetime(2026, 11, 21, 12, 0, 0, tzinfo=timezone.utc)
    fmt = outpost.advisory.fmt
    entry = json.loads((workspace / "space-reclamation/data/examples/example-entry.json").read_text(encoding="utf-8"))

    log("1. space-reclamation -> assignment")
    offer = ok("capture assignment", bridge.entry_to_assignment(
        entry, task_id="T-0042", node="A1", coordinator="fleet-coordinator", seq=95,
        timestamp=fmt(now), accept_by=fmt(now + timedelta(seconds=10))))

    log("2. satnav-swarm: fix the reclaimer from ranges, report its location")
    anchors = [(0.0, 0.0, 0.0), (100.0, 0.0, 0.0), (0.0, 100.0, 0.0), (0.0, 0.0, 100.0), (80.0, 90.0, 70.0)]
    r_orbit = 6378.137 + 825.0
    truth = (r_orbit, 0.0, 0.0)
    # Anchors are offsets (km) from the reclaimer's orbital position in this toy frame.
    shifted = [(truth[0] + a[0], truth[1] + a[1], truth[2] + a[2]) for a in anchors]
    ranges = [math.dist(truth, s) for s in shifted]
    fix = satnav.solve_position(shifted, ranges)
    assert fix.converged and math.dist(fix.position, truth) < 1e-6
    inc = math.radians(51.6)
    loc = satnav.location_from_earth_state(fix.position, (0.0, 7.4 * math.cos(inc), 7.4 * math.sin(inc)))
    assert loc["zone"] == offer["task"]["location"]["zone"] == "LEO"
    status = {"version": "OTF-1", "kind": "status", "timestamp": fmt(now + timedelta(seconds=5)),
              "source": {"id": "A1", "role": "node"}, "seq": 412,
              "node": {"type": "reclaimer", "mode": "nominal", "phase": "Capturing",
                       "link": "connected", "capabilities": ["capture", "deorbit"]},
              "location": loc, "task": {"id": "T-0042", "state": "active", "progress": 0.4}}
    ok("reclaimer status", status)

    log("3. outpost-core: depot answers its own offer, ingests the capture")
    depot = outpost.OutpostNode("depot-1", outpost.PowerBudget(capacity_wh=10_000, soc_wh=9_000))
    ok("depot status", depot.status(now))
    depot_offer = {**offer, "destination": "depot-1",
                   "task": {**offer["task"], "id": "T-0043", "action": "process"}}
    ok("depot offer", depot_offer)
    ok("depot ack", depot.handle_assignment(depot_offer, now))
    event = {"version": "OTF-1", "timestamp": fmt(now + timedelta(seconds=22)),
             "mission": {"id": "orbital-demo-1", "podId": "A1", "type": "reclaimer"},
             "location": loc, "target": offer["task"]["target"], "action": "captured",
             "outcome": {"processedKg": 5.0, "repurposedAs": "shield_block", "status": "stored"},
             "certifications": {"SMESSC": True, "ODCI_contribution": 5.0}, "taskId": "T-0042"}
    ok("capture event", event)
    depot.ingest_event(event)
    summary = bridge.feedstock_summary([event])
    assert dict(depot.inventory_kg) == summary["kg_by_product"] == {"shield_block": 5.0}
    log(f"   depot inventory == registry feedstock summary: {summary['kg_by_product']}")

    log("4. outpost-core -> ai-roundtable: equal-priority contention becomes a Tier 1 advisory")
    sched = outpost.DockingCoordinator([outpost.Port("P0")]).schedule([
        outpost.DockRequest("A1", "dock", 5, eta_s=0, duration_s=600),
        outpost.DockRequest("M1", "dock", 5, eta_s=30, duration_s=600)])
    (contention,) = sched.contentions
    request = outpost.contention_to_advisory(contention, "depot-1", now, now + timedelta(hours=1))
    problems = adv.check(request)
    assert not problems, problems
    log(f"   advisory {request['id']}: default '{request['defaultChoice']}' stands unless a human approves")

    emergency = outpost.DockingCoordinator([outpost.Port("P0")]).schedule([
        outpost.DockRequest("A1", "dock", 10, 0, 600), outpost.DockRequest("M1", "dock", 10, 0, 600)])
    assert outpost.contention_to_advisory(emergency.contentions[0], "depot-1", now, now + timedelta(hours=1)) is None
    log("   emergency contention stays deterministic (Tier 0): no advisory generated")

    log("5. ai-roundtable: that same request through the Jac engine (scripted models stand in for LLMs)")
    recommendation = run_roundtable(workspace, request, now, adv, log)

    return {"otf1_packets_checked": checked, "feedstock": summary, "advisory": request,
            "recommendation": recommendation}


def run_roundtable(workspace: Path, request: dict, now: datetime, adv, log):
    """Run the roundtable engine on `request` and check what comes back against the ADV-1
    contract. The models are byllm's scripted `mockllm`, so this proves the plumbing between
    the repos (not that any real model reasons well). Returns None, with a note, when jaclang
    or byllm is not installed."""
    try:
        import jaclang  # noqa: F401  (installs the .jac import hook; must precede byllm)
        from byllm.lib import MockRawResponse, Model
    except ImportError:
        log("   skipped: pip install -r ai-roundtable/jac/requirements.txt to run the engine here")
        return None
    sys.path.insert(0, str(workspace / "ai-roundtable" / "jac"))
    from roundtable.brain import Brain
    from roundtable.clock import Clock
    from roundtable.engine import RunConfig, run_session
    from roundtable.roster import AgentSeat, Roster
    from roundtable.spec import AgentSpec

    def say(**fields):
        return MockRawResponse(content=json.dumps(fields))

    def seat(role, outputs, critic=False):
        spec = AgentSpec(role=role, brief=f"{role} (scripted)", model_name="mockllm",
                         temperature=0.2, critic=critic, topics=[])
        return AgentSeat(spec=spec, brain=Brain(model=Model(model_name="mockllm", config={"outputs": outputs})))

    def position(choice, conf):
        return say(choice=choice, rationale="scripted", confidence=conf, risks=[], references=[])

    def vote(choice, conf):
        return say(choice=choice, rationale="scripted", confidence=conf)

    seats = [
        seat("Logistics Officer", [position("swap", 0.7), position("swap", 0.7), vote("swap", 0.7)]),
        seat("Resource Economist", [position("swap", 0.6), position("swap", 0.6), vote("swap", 0.6)]),
        seat("Safety Officer", [say(issues=["arrival ETA for M1 is uncertain"], blocks=[], cases=[]),
                                vote("default", 0.5)], critic=True),
    ]
    roster = Roster(seats=seats, briefer=seat("Briefer", ["Scripted briefing."]))
    outcome = run_session(request, roster, RunConfig(), Clock(fixed=now))
    assert outcome.status == "recommended", outcome.reasons
    rec = outcome.recommendation
    problems = adv.check(rec, request)
    assert not problems, problems
    assert rec["requiresHumanApproval"] is True and rec["recommendation"] in {"default", "swap"}
    log(f"   valid ADV-1 recommendation: '{rec['recommendation']}' by {rec['process']['basis']}; "
        f"{rec['nextActions'][0]}")
    return rec


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--workspace", type=Path, default=Path(__file__).resolve().parent.parent.parent)
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)
    result = run(args.workspace.resolve(), log=(lambda *_: None) if args.quiet else print)
    print(f"OK: {len(result['otf1_packets_checked'])} OTF-1 packets valid; scenario consistent across repos")
    return 0


if __name__ == "__main__":
    sys.exit(main())
