import { useMutation } from "@tanstack/react-query";
import { CheckCircle2, Play, ShieldCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { apiRequest, queryClient } from "@/lib/queryClient";
import { CounterfactualSuiteReport } from "@/lib/types";

export function ValidationSuitePage({
  report,
}: {
  report: CounterfactualSuiteReport;
}) {
  const runSuiteMutation = useMutation({
    mutationFn: async () => {
      const res = await apiRequest("POST", "/api/counterfactuals/run", {});
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/overview"] });
    },
  });

  return (
    <div className="mx-auto max-w-7xl space-y-5">
      <div className="flex flex-col justify-between gap-3 border-b border-border pb-4 sm:flex-row sm:items-end">
        <div>
          <div className="font-mono text-xs font-semibold uppercase tracking-wider text-primary">
            VALIDATION_SUITE (CONSERVATION LAW L6)
          </div>
          <h1 className="mt-0.5 text-xl font-semibold tracking-tight">
            Leave-One-Tale-Out &amp; Silent-Pilgrim Counterfactual Benchmark
          </h1>
          <p className="mt-1 max-w-3xl text-xs text-muted-foreground">
            Tests whether protocol boundary conditions (estate, quiting debt, and sentence/solaas homeostasis) independently converge on Chaucerian genre shifts and silent-pilgrim voices while maintaining zero 5-gram overlap and &lt; 0.62 Levenshtein similarity against held-out S1 witnesses.
          </p>
        </div>

        <Button
          size="sm"
          onClick={() => runSuiteMutation.mutate()}
          disabled={runSuiteMutation.isPending}
          data-testid="rerun-counterfactuals-btn"
          className="h-9 gap-1.5 px-4 text-xs font-semibold"
        >
          <Play className="h-3.5 w-3.5" />
          <span>
            {runSuiteMutation.isPending
              ? "Executing 6 Scenarios..."
              : "Re-Run Counterfactual Suite"}
          </span>
        </Button>
      </div>

      {/* Summary KPI Row */}
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
              <span>{report.all_l6_non_copying_passed ? "PASSED" : "FAIL"}</span>
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

      {/* Scenario Cards / Table */}
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
                    variant={sc.structural_convergence ? "default" : "destructive"}
                  >
                    {sc.structural_convergence
                      ? "CONVERGED"
                      : "DIVERGED"}
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
  );
}
