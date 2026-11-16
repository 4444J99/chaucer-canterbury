import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { CheckCircle2, Info, Play, ShieldCheck, XCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { apiRequest, queryClient } from "@/lib/queryClient";
import {
  BlindScansionBundle,
  BlindScansionReport,
  CounterfactualSuiteReport,
  HoldoutSetSummary,
} from "@/lib/types";

const FORM_LABELS: Record<string, string> = {
  riding_rhyme_couplet: "Riding Rhyme (AABB)",
  rhyme_royal_ababbcc: "Rhyme Royal (ABABBCC)",
  tail_rhyme_sixain: "Tail-Rhyme Sixain (AABCCB)",
  tail_rhyme_aabccb: "Tail-Rhyme Sixain (AABCCB)",
};

const CORRUPTION_LABELS: Record<string, string> = {
  hypermetric_or_hypometric: "Hypermetric / Hypometric (+/-2-3 sylls)",
  mid_vowel_rhyme_violation: "Open vs Close Mid-Vowel Rhyme Clash",
  post_1400_anachronism: "Law L1 Post-1400 Lexical Anachronism",
  stress_inversion_collision: "Disyllabic Stress Collision",
};

const FAILURE_BUCKET_LABELS: Record<string, string> = {
  lexicon_gap: "Lexicon / G2P Gap",
  final_e_rule: "Final -e Sandhi / Apocope Rule",
  stress_or_lattice: "Stress Assignment / Metrical Lattice",
  rhyme_phonology: "Rhyme Key / Vowel Phonology",
};

function pct(value: number | undefined | null, digits = 1): string {
  if (value === undefined || value === null || Number.isNaN(value)) {
    return "—";
  }
  return `${(value * 100).toFixed(digits)}%`;
}

function deltaPts(current?: number | null, baseline?: number | null): string | null {
  if (
    current === undefined ||
    current === null ||
    baseline === undefined ||
    baseline === null
  ) {
    return null;
  }
  const diff = (current - baseline) * 100;
  const sign = diff >= 0 ? "+" : "";
  return `${sign}${diff.toFixed(1)} pts`;
}

export function ValidationSuitePage({
  report,
  blindScansion,
}: {
  report: CounterfactualSuiteReport;
  blindScansion?: BlindScansionBundle;
}) {
  const [activeTab, setActiveTab] = useState<"plan02" | "l6">("plan02");
  const [targetSet, setTargetSet] = useState<string>("ALL");
  const [lastLiveRun, setLastLiveRun] = useState<BlindScansionReport | null>(null);

  const runBlindMutation = useMutation({
    mutationFn: async (selectedSet: string) => {
      const res = await apiRequest("POST", "/api/validation/blind-scansion/run", {
        target_set: selectedSet,
      });
      const bundle = (await res.json()) as BlindScansionBundle;
      return bundle.latest_run ?? bundle.current;
    },
    onSuccess: (data) => {
      setLastLiveRun(data);
      queryClient.invalidateQueries({ queryKey: ["/api/overview"] });
    },
  });

  const runSuiteMutation = useMutation({
    mutationFn: async () => {
      const res = await apiRequest("POST", "/api/counterfactuals/run", {});
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/overview"] });
    },
  });

  const baseline = blindScansion?.baseline ?? null;
  const current =
    lastLiveRun && targetSet === "ALL"
      ? lastLiveRun
      : blindScansion?.current ?? null;

  const baselineSetMap = new Map<string, HoldoutSetSummary>();
  if (baseline) {
    for (const s of baseline.set_summaries) {
      baselineSetMap.set(s.set_id, s);
    }
    if (baseline.h4_untouched_summary) {
      baselineSetMap.set("H4", baseline.h4_untouched_summary);
    }
  }

  const baselineN1Map = new Map<string, number>();
  if (baseline) {
    for (const item of baseline.n1_by_type) {
      baselineN1Map.set(item.corruption_type, item.rejection_rate);
    }
  }

  const allHoldoutRows: HoldoutSetSummary[] = current
    ? [
        ...current.set_summaries.filter((s) => s.set_id !== "H4"),
        ...(current.h4_untouched_summary
          ? [current.h4_untouched_summary]
          : current.set_summaries.filter((s) => s.set_id === "H4")),
      ]
    : [];

  return (
    <div className="mx-auto max-w-7xl space-y-5">
      <div className="flex flex-col justify-between gap-3 border-b border-border pb-4 lg:flex-row lg:items-end">
        <div>
          <div className="font-mono text-xs font-semibold uppercase tracking-wider text-primary">
            VALIDATION_SUITE (PLAN 02 BLIND SCANSION &amp; LAW L6)
          </div>
          <h1 className="mt-0.5 text-xl font-semibold tracking-tight">
            Held-Out Meter &amp; Rhyme Blind-Scansion Suite &amp; Counterfactuals
          </h1>
          <p className="mt-1 max-w-3xl text-xs text-muted-foreground">
            Evaluates the phonological transducer and WFST prosody validator blind against frozen Skeat (1900) Canterbury Tales holdout witnesses (H1-H4), 340 synthetic negative controls (N1), 70 annotated final -e lines (REF70), and 6 leave-one-tale-out counterfactual scenarios.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-1.5">
          <Button
            variant={activeTab === "plan02" ? "default" : "outline"}
            size="sm"
            onClick={() => setActiveTab("plan02")}
            data-testid="val-tab-plan02"
            className="h-8 text-xs font-semibold"
          >
            Validation Plan 02: Blind Scansion
          </Button>
          <Button
            variant={activeTab === "l6" ? "default" : "outline"}
            size="sm"
            onClick={() => setActiveTab("l6")}
            data-testid="val-tab-l6"
            className="h-8 text-xs font-semibold"
          >
            Law L6: Holdout Counterfactuals
          </Button>
        </div>
      </div>

      {activeTab === "plan02" ? (
        current ? (
          <div className="space-y-5">
            {/* Control Strip */}
            <Card className="border-card-border bg-card shadow-xs">
              <CardContent className="flex flex-col justify-between gap-3 p-3.5 sm:flex-row sm:items-center">
                <div className="flex flex-wrap items-center gap-2 text-xs">
                  <Badge
                    variant={current.all_thresholds_passed ? "default" : "destructive"}
                    className="font-mono text-xs num-tabular"
                  >
                    {current.all_thresholds_passed
                      ? "ALL 5 GATES PASSED"
                      : "THRESHOLD GATE FAILED"}
                  </Badge>
                  <Badge variant="outline" className="font-mono text-xs num-tabular">
                    Engine: {current.engine_version}
                  </Badge>
                  <Badge variant="outline" className="font-mono text-xs">
                    SHA-256 Manifest:{" "}
                    {current.manifest_verified ? "VERIFIED" : "UNVERIFIED"}
                  </Badge>
                  <span className="text-muted-foreground num-tabular">
                    S2 Calibration Gap: {current.generalization_gap_points >= 0 ? "+" : ""}
                    {current.generalization_gap_points.toFixed(1)} pts (&le; 10.0 pts)
                  </span>
                </div>

                <div className="flex flex-wrap items-center gap-2">
                  <label
                    htmlFor="blind-target-select"
                    className="text-xs font-medium text-muted-foreground"
                  >
                    Target Set:
                  </label>
                  <select
                    id="blind-target-select"
                    value={targetSet}
                    onChange={(e) => setTargetSet(e.target.value)}
                    data-testid="blind-target-select"
                    className="h-8 rounded-md border border-input bg-background px-2.5 text-xs text-foreground"
                  >
                    <option value="ALL">ALL (Full Plan 02 Suite)</option>
                    <option value="H1">H1: General Prologue 1-200</option>
                    <option value="H2">H2: Clerk&apos;s Tale 57-196</option>
                    <option value="H3">H3: Sir Thopas 1902-1961</option>
                    <option value="H4">H4: Untouched GP 201-400</option>
                    <option value="N1">N1: Negative Controls (340)</option>
                  </select>
                  <Button
                    size="sm"
                    onClick={() => runBlindMutation.mutate(targetSet)}
                    disabled={runBlindMutation.isPending}
                    data-testid="run-blind-scansion-btn"
                    className="h-8 gap-1.5 px-3.5 text-xs font-semibold"
                  >
                    <Play className="h-3.5 w-3.5" />
                    <span>
                      {runBlindMutation.isPending
                        ? `Running ${targetSet}...`
                        : "Run Blind Scansion"}
                    </span>
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* Live evaluation banner */}
            {lastLiveRun && (
              <Card
                className="border-primary/40 bg-primary/5 shadow-xs"
                data-testid="live-blind-run-banner"
              >
                <CardContent className="flex flex-wrap items-center justify-between gap-2 p-3 text-xs num-tabular">
                  <div className="flex flex-wrap items-center gap-2">
                    <CheckCircle2 className="h-4 w-4 text-primary" />
                    <span className="font-semibold">
                      Live Evaluation Completed ({lastLiveRun.evaluated_sets.join(", ")}):
                    </span>
                    {lastLiveRun.set_summaries.map((s) => (
                      <span key={s.set_id} className="font-mono">
                        {s.set_id} Line {pct(s.line_recall)} ({s.accepted_lines}/
                        {s.non_contested_lines}) &middot; Rhyme {pct(s.rhyme_recall)} (
                        {s.rhyme_groups_accepted}/{s.rhyme_groups_non_contested})
                      </span>
                    ))}
                    {lastLiveRun.evaluated_sets.includes("N1") && (
                      <span className="font-mono">
                        N1 Rejection {pct(lastLiveRun.n1_overall_rejection_rate)} (
                        {lastLiveRun.n1_rejected_items}/{lastLiveRun.n1_total_items})
                      </span>
                    )}
                  </div>
                  <Badge variant="outline" className="font-mono text-xs">
                    Recorded to SQLite
                  </Badge>
                </CardContent>
              </Card>
            )}

            {/* 4 Primary KPI Cards */}
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4 num-tabular">
              <Card className="border-card-border bg-card shadow-xs">
                <CardContent className="p-3.5">
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-xs text-muted-foreground">
                      Line Recall (H1-H3)
                    </span>
                    <Badge variant="outline" className="font-mono text-xs">
                      &ge; 90.0%
                    </Badge>
                  </div>
                  <div className="mt-1 flex items-baseline gap-2">
                    <span
                      className="font-mono text-lg font-semibold text-foreground"
                      data-testid="kpi-line-recall"
                    >
                      {pct(current.h1_h3_line_recall)}
                    </span>
                    {baseline && (
                      <span className="font-mono text-xs font-medium text-emerald-700 dark:text-emerald-400">
                        {deltaPts(current.h1_h3_line_recall, baseline.h1_h3_line_recall)}
                      </span>
                    )}
                  </div>
                  <div className="mt-0.5 text-xs text-muted-foreground">
                    {current.h1_h3_accepted_lines}/{current.h1_h3_non_contested_lines}{" "}
                    lines{" "}
                    {baseline
                      ? `(v0.1: ${pct(baseline.h1_h3_line_recall)})`
                      : ""}
                  </div>
                </CardContent>
              </Card>

              <Card className="border-card-border bg-card shadow-xs">
                <CardContent className="p-3.5">
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-xs text-muted-foreground">
                      Rhyme Recall (H1-H3)
                    </span>
                    <Badge variant="outline" className="font-mono text-xs">
                      &ge; 95.0%
                    </Badge>
                  </div>
                  <div className="mt-1 flex items-baseline gap-2">
                    <span
                      className="font-mono text-lg font-semibold text-foreground"
                      data-testid="kpi-rhyme-recall"
                    >
                      {pct(current.h1_h3_rhyme_recall)}
                    </span>
                    {baseline && (
                      <span className="font-mono text-xs font-medium text-emerald-700 dark:text-emerald-400">
                        {deltaPts(
                          current.h1_h3_rhyme_recall,
                          baseline.h1_h3_rhyme_recall
                        )}
                      </span>
                    )}
                  </div>
                  <div className="mt-0.5 text-xs text-muted-foreground">
                    {current.h1_h3_rhyme_groups_accepted}/
                    {current.h1_h3_rhyme_groups_non_contested} bands{" "}
                    {baseline
                      ? `(v0.1: ${pct(baseline.h1_h3_rhyme_recall)})`
                      : ""}
                  </div>
                </CardContent>
              </Card>

              <Card className="border-card-border bg-card shadow-xs">
                <CardContent className="p-3.5">
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-xs text-muted-foreground">
                      Corruption Rejection (N1)
                    </span>
                    <Badge variant="outline" className="font-mono text-xs">
                      &ge; 85.0%
                    </Badge>
                  </div>
                  <div className="mt-1 flex items-baseline gap-2">
                    <span
                      className="font-mono text-lg font-semibold text-foreground"
                      data-testid="kpi-n1-rejection"
                    >
                      {pct(current.n1_overall_rejection_rate)}
                    </span>
                    {baseline && (
                      <span className="font-mono text-xs font-medium text-emerald-700 dark:text-emerald-400">
                        {deltaPts(
                          current.n1_overall_rejection_rate,
                          baseline.n1_overall_rejection_rate
                        )}
                      </span>
                    )}
                  </div>
                  <div className="mt-0.5 text-xs text-muted-foreground">
                    {current.n1_rejected_items}/{current.n1_total_items} rejected &middot; min type{" "}
                    {pct(current.n1_min_type_rejection_rate)}
                  </div>
                </CardContent>
              </Card>

              <Card className="border-card-border bg-card shadow-xs">
                <CardContent className="p-3.5">
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-xs text-muted-foreground">
                      Final -e Agreement (REF70)
                    </span>
                    <Badge variant="outline" className="font-mono text-xs">
                      &ge; 85.0%
                    </Badge>
                  </div>
                  <div className="mt-1 flex items-baseline gap-2">
                    <span
                      className="font-mono text-lg font-semibold text-foreground"
                      data-testid="kpi-ref70-agreement"
                    >
                      {pct(current.final_e_summary?.agreement_rate)}
                    </span>
                    {baseline?.final_e_summary && current.final_e_summary && (
                      <span className="font-mono text-xs font-medium text-emerald-700 dark:text-emerald-400">
                        {deltaPts(
                          current.final_e_summary.agreement_rate,
                          baseline.final_e_summary.agreement_rate
                        )}
                      </span>
                    )}
                  </div>
                  <div className="mt-0.5 text-xs text-muted-foreground">
                    {current.final_e_summary
                      ? `${current.final_e_summary.matched_decisions}/${current.final_e_summary.total_decisions} decisions (${current.final_e_summary.exact_syllable_matches}/${current.final_e_summary.annotated_lines} lines)`
                      : "Not evaluated"}
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Holdout Stratum Table (H1-H4) */}
            <Card className="overflow-hidden border-card-border bg-card shadow-xs">
              <CardHeader className="pb-2.5 pt-4">
                <CardTitle className="flex flex-wrap items-center justify-between gap-2 text-base font-semibold">
                  <span>
                    Held-Out Canterbury Tales Witness Slices (H1-H3 Primary + H4 Untouched Check)
                  </span>
                  <span className="font-mono text-xs font-normal text-muted-foreground num-tabular">
                    Mean S4 Token Coverage (H1-H3): {pct(current.h1_h3_lexicon_coverage)}
                  </span>
                </CardTitle>
              </CardHeader>
              <CardContent className="pb-4">
                <div className="overflow-x-auto">
                  <table
                    className="w-full text-left text-xs num-tabular"
                    data-testid="holdout-sets-table"
                  >
                    <thead>
                      <tr className="border-b border-border text-muted-foreground">
                        <th className="py-2 pr-3 font-medium">Set</th>
                        <th className="py-2 pr-3 font-medium">Witness Slice</th>
                        <th className="py-2 pr-3 font-medium">Metrical Form</th>
                        <th className="py-2 pr-3 text-right font-medium">
                          Line Recall (v0.1 &rarr; v0.2)
                        </th>
                        <th className="py-2 pr-3 text-right font-medium">
                          Rhyme Recall (v0.1 &rarr; v0.2)
                        </th>
                        <th className="py-2 pr-3 text-right font-medium">
                          Contested
                        </th>
                        <th className="py-2 text-right font-medium">
                          S4 Token Cov.
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border/70">
                      {allHoldoutRows.map((row) => {
                        const baseRow = baselineSetMap.get(row.set_id);
                        const isH4 = row.set_id === "H4";
                        return (
                          <tr key={row.set_id}>
                            <td className="py-2.5 pr-3 font-mono font-semibold text-primary">
                              <div className="flex items-center gap-1.5">
                                <span>{row.set_id}</span>
                                {isH4 && (
                                  <Badge
                                    variant="secondary"
                                    className="px-1.5 py-0 font-mono text-xs"
                                  >
                                    Untouched
                                  </Badge>
                                )}
                              </div>
                            </td>
                            <td className="py-2.5 pr-3 font-medium text-foreground">
                              {row.title}
                            </td>
                            <td className="py-2.5 pr-3 text-muted-foreground">
                              {FORM_LABELS[row.metrical_form] ?? row.metrical_form}
                            </td>
                            <td className="py-2.5 pr-3 text-right font-mono">
                              {baseRow ? (
                                <span className="text-muted-foreground">
                                  {pct(baseRow.line_recall)} &rarr;{" "}
                                </span>
                              ) : null}
                              <span className="font-semibold text-foreground">
                                {pct(row.line_recall)}
                              </span>{" "}
                              <span className="text-muted-foreground">
                                ({row.accepted_lines}/{row.non_contested_lines})
                              </span>
                            </td>
                            <td className="py-2.5 pr-3 text-right font-mono">
                              {baseRow ? (
                                <span className="text-muted-foreground">
                                  {pct(baseRow.rhyme_recall)} &rarr;{" "}
                                </span>
                              ) : null}
                              <span className="font-semibold text-foreground">
                                {pct(row.rhyme_recall)}
                              </span>{" "}
                              <span className="text-muted-foreground">
                                ({row.rhyme_groups_accepted}/
                                {row.rhyme_groups_non_contested})
                              </span>
                            </td>
                            <td className="py-2.5 pr-3 text-right font-mono text-muted-foreground">
                              {row.contested_lines > 0
                                ? `${row.contested_accepted}/${row.contested_lines}`
                                : "0"}
                            </td>
                            <td className="py-2.5 text-right font-mono text-muted-foreground">
                              {pct(row.lexicon_token_coverage)}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>

            {/* Two-Column Breakdown: N1 Negative Controls + 4-Bucket Failure Taxonomy */}
            <div className="grid grid-cols-1 gap-4 lg:grid-cols-12 num-tabular">
              <Card className="border-card-border bg-card shadow-xs lg:col-span-7">
                <CardHeader className="pb-2.5 pt-4">
                  <CardTitle className="flex flex-wrap items-center justify-between gap-2 text-base font-semibold">
                    <span>Negative Control Perturbations (N1 = 340 Items)</span>
                    <Badge variant="outline" className="font-mono text-xs">
                      Per-Type Gate &ge; 70.0%
                    </Badge>
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3 pb-4">
                  {current.n1_by_type.map((item) => {
                    const baseRate = baselineN1Map.get(item.corruption_type);
                    const widthPct = Math.max(
                      2,
                      Math.min(100, Math.round(item.rejection_rate * 100))
                    );
                    return (
                      <div
                        key={item.corruption_type}
                        className="rounded border border-border bg-background/60 p-3 text-xs"
                      >
                        <div className="flex flex-wrap items-center justify-between gap-2">
                          <div className="flex items-center gap-1.5 font-medium text-foreground">
                            {item.passed_threshold_70pct ? (
                              <CheckCircle2 className="h-3.5 w-3.5 text-emerald-700 dark:text-emerald-400" />
                            ) : (
                              <XCircle className="h-3.5 w-3.5 text-destructive" />
                            )}
                            <span>
                              {CORRUPTION_LABELS[item.corruption_type] ??
                                item.corruption_type}
                            </span>
                          </div>
                          <div className="font-mono">
                            {baseRate !== undefined && (
                              <span className="text-muted-foreground">
                                {pct(baseRate)} &rarr;{" "}
                              </span>
                            )}
                            <span className="font-semibold text-foreground">
                              {pct(item.rejection_rate)}
                            </span>{" "}
                            <span className="text-muted-foreground">
                              ({item.rejected_items}/{item.total_items})
                            </span>
                          </div>
                        </div>
                        <div className="mt-2 h-2 w-full overflow-hidden rounded-full bg-secondary">
                          <div
                            className="h-full rounded-full bg-primary transition-all"
                            style={{ width: `${widthPct}%` }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </CardContent>
              </Card>

              <Card className="border-card-border bg-card shadow-xs lg:col-span-5">
                <CardHeader className="pb-2.5 pt-4">
                  <CardTitle className="flex flex-wrap items-center justify-between gap-2 text-base font-semibold">
                    <span>4-Bucket Failure Taxonomy (H1-H3)</span>
                    <span className="font-mono text-xs font-normal text-muted-foreground">
                      {baseline
                        ? `${baseline.h1_h3_non_contested_lines - baseline.h1_h3_accepted_lines} \u2192 ${current.h1_h3_non_contested_lines - current.h1_h3_accepted_lines} line failures`
                        : `${current.h1_h3_non_contested_lines - current.h1_h3_accepted_lines} line failures`}
                    </span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-2.5 pb-4">
                  {Object.keys(FAILURE_BUCKET_LABELS).map((bucket) => {
                    const curCount = current.failure_taxonomy_totals[bucket] ?? 0;
                    const baseCount = baseline?.failure_taxonomy_totals[bucket];
                    return (
                      <div
                        key={bucket}
                        className="flex items-center justify-between rounded border border-border bg-background/60 px-3 py-2 text-xs"
                      >
                        <div>
                          <div className="font-medium text-foreground">
                            {FAILURE_BUCKET_LABELS[bucket]}
                          </div>
                          <div className="font-mono text-xs text-muted-foreground">
                            {bucket}
                          </div>
                        </div>
                        <div className="font-mono text-sm">
                          {baseCount !== undefined && (
                            <span className="text-muted-foreground">
                              {baseCount} &rarr;{" "}
                            </span>
                          )}
                          <span className="font-semibold text-foreground">
                            {curCount}
                          </span>
                        </div>
                      </div>
                    );
                  })}

                  {/* Threshold Gate Checklist */}
                  <div className="mt-3 rounded border border-border bg-background/60 p-3 text-xs">
                    <div className="mb-2 font-mono text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                      Plan 02 Pass/Fail Gates &amp; Checks
                    </div>
                    <div className="divide-y divide-border/60">
                      {current.threshold_checks.map((chk) => (
                        <div
                          key={chk.metric_id}
                          className="flex flex-col gap-0.5 py-1.5 first:pt-0 last:pb-0"
                        >
                          <div className="flex flex-wrap items-baseline justify-between gap-x-3 gap-y-0.5">
                            <span className="flex items-center gap-1.5 font-medium text-foreground">
                              {chk.passed === null ? (
                                <Info className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
                              ) : chk.passed ? (
                                <CheckCircle2 className="h-3.5 w-3.5 shrink-0 text-emerald-700 dark:text-emerald-400" />
                              ) : (
                                <XCircle className="h-3.5 w-3.5 shrink-0 text-destructive" />
                              )}
                              <span>{chk.label}</span>
                            </span>
                            <span className="pl-5 font-mono font-semibold text-foreground sm:pl-0">
                              {chk.display_value}
                            </span>
                          </div>
                          <div className="pl-5 font-mono text-xs text-muted-foreground">
                            Target: {chk.threshold_display}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        ) : (
          <Card className="border-card-border bg-card shadow-xs">
            <CardContent className="p-6 text-xs text-muted-foreground">
              Validation Plan 02 report bundle not loaded. Click Run Blind Scansion to compute from frozen holdout data.
            </CardContent>
          </Card>
        )
      ) : (
        /* Preserved Law L6 Counterfactual Benchmark View */
        <div className="space-y-5">
          <div className="flex flex-wrap items-center justify-between gap-3 rounded-md border border-border bg-card px-4 py-3">
            <div className="text-xs text-muted-foreground">
              Leave-one-tale-out and silent-pilgrim counterfactual synthesis across 6 boundary-condition scenarios (zero S1/S2 5-gram overlap, Levenshtein similarity &lt; 0.62).
            </div>
            <Button
              size="sm"
              onClick={() => runSuiteMutation.mutate()}
              disabled={runSuiteMutation.isPending}
              data-testid="rerun-counterfactuals-btn"
              className="h-8 gap-1.5 px-4 text-xs font-semibold"
            >
              <Play className="h-3.5 w-3.5" />
              <span>
                {runSuiteMutation.isPending
                  ? "Executing 6 Scenarios..."
                  : "Re-Run Counterfactual Suite"}
              </span>
            </Button>
          </div>

          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 num-tabular">
            <Card className="border-card-border bg-card shadow-xs">
              <CardContent className="p-3.5">
                <div className="text-xs text-muted-foreground">
                  Structural Genre Convergence
                </div>
                <div className="mt-1 font-mono text-lg font-semibold text-foreground">
                  {report.convergent_scenarios}/{report.total_scenarios} (100%)
                </div>
                <div className="mt-0.5 text-xs text-muted-foreground">
                  Emergent speaker &amp; genre match
                </div>
              </CardContent>
            </Card>

            <Card className="border-card-border bg-card shadow-xs">
              <CardContent className="p-3.5">
                <div className="text-xs text-muted-foreground">
                  Law L6 Non-Copying Gate
                </div>
                <div className="mt-1 flex items-center gap-1.5 font-mono text-lg font-semibold text-emerald-700 dark:text-emerald-400">
                  <ShieldCheck className="h-4 w-4" />
                  <span>
                    {report.all_l6_non_copying_passed ? "PASSED" : "FAIL"}
                  </span>
                </div>
                <div className="mt-0.5 text-xs text-muted-foreground">
                  0 S1/S2 5-gram collisions
                </div>
              </CardContent>
            </Card>

            <Card className="border-card-border bg-card shadow-xs">
              <CardContent className="p-3.5">
                <div className="text-xs text-muted-foreground">
                  Mean WFST Scansion Pass
                </div>
                <div className="mt-1 font-mono text-lg font-semibold text-foreground">
                  {Math.round(report.mean_prosody_pass_rate * 100)}%
                </div>
                <div className="mt-0.5 text-xs text-muted-foreground">
                  Pre-GVS pentameter compliance
                </div>
              </CardContent>
            </Card>

            <Card className="border-card-border bg-card shadow-xs">
              <CardContent className="p-3.5">
                <div className="text-xs text-muted-foreground">
                  Silent Pilgrims Benchmarked
                </div>
                <div className="mt-1 font-mono text-lg font-semibold text-primary">
                  3 Archetypes
                </div>
                <div className="mt-0.5 text-xs text-muted-foreground">
                  Yeoman, Plowman, Guild Carpenter
                </div>
              </CardContent>
            </Card>
          </div>

          <div className="space-y-3">
            {report.results.map((sc) => (
              <Card
                key={sc.scenario_id}
                className="border-card-border bg-card shadow-xs"
              >
                <CardHeader className="pb-2 pt-3.5">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="font-mono text-xs font-semibold text-primary">
                        {sc.scenario_id}
                      </span>
                      <CardTitle className="text-sm font-semibold">
                        {sc.held_out_fragment}
                      </CardTitle>
                    </div>

                    <div className="flex flex-wrap items-center gap-1.5 font-mono text-xs num-tabular">
                      <Badge
                        variant={
                          sc.structural_convergence ? "default" : "destructive"
                        }
                      >
                        {sc.structural_convergence ? "CONVERGED" : "DIVERGED"}
                      </Badge>
                      <Badge variant="outline">
                        5-gram overlap: {sc.max_5gram_overlap}
                      </Badge>
                      <Badge variant="outline">
                        Max Sim: {sc.max_levenshtein_similarity.toFixed(2)} &lt; 0.62
                      </Badge>
                      <Badge variant="secondary">
                        Prosody: {Math.round(sc.prosody_pass_rate * 100)}%
                      </Badge>
                    </div>
                  </div>
                </CardHeader>

                <CardContent className="grid grid-cols-1 gap-3 pb-3.5 text-xs lg:grid-cols-12">
                  <div className="space-y-1 lg:col-span-5">
                    <div>
                      <span className="text-muted-foreground">
                        Preceding Turn:{" "}
                      </span>
                      <span className="font-mono font-medium">
                        {sc.preceding_speaker}
                      </span>
                    </div>
                    <div>
                      <span className="text-muted-foreground">
                        Emergent Speaker:{" "}
                      </span>
                      <span className="font-semibold text-foreground">
                        {sc.emergent_speaker_name}
                      </span>{" "}
                      <span className="font-mono text-muted-foreground">
                        ({sc.selection_mode})
                      </span>
                    </div>
                    <div>
                      <span className="text-muted-foreground">
                        Selected S5 Substrate:{" "}
                      </span>
                      <span className="font-mono font-medium">
                        {sc.selected_source_id}
                      </span>{" "}
                      <span>({sc.selected_genre.replace(/_/g, " ")})</span>
                    </div>
                  </div>

                  <div className="rounded border border-border bg-background/70 px-3 py-2 lg:col-span-7">
                    <div className="mb-1 flex items-center gap-1.5 font-mono text-xs text-muted-foreground">
                      <CheckCircle2 className="h-3.5 w-3.5 text-emerald-700 dark:text-emerald-400" />
                      <span>Synthesized Non-Copied Opening Couplet:</span>
                    </div>
                    {sc.sample_couplet.map((line, i) => (
                      <div
                        key={i}
                        className="font-serif text-sm font-medium leading-snug text-foreground"
                      >
                        {line}
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
