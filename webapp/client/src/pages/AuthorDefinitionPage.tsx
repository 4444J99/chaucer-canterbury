import { useEffect, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { RotateCcw, Save } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { apiRequest, queryClient } from "@/lib/queryClient";
import { AuthorDefinition } from "@/lib/types";

const ETYMON_LABELS: Record<string, string> = {
  OE: "Old English (Germanic Core)",
  OF: "Old French (Continental Prestige)",
  AN: "Anglo-Norman (Insular Legal/Civic)",
  LAT: "Latin (Scholastic & Homiletic)",
  ON: "Old Norse (Northern & Everyday)",
};

export function AuthorDefinitionPage({
  author,
}: {
  author: AuthorDefinition;
}) {
  const [v2Rate, setV2Rate] = useState(author.v2_topicalization_rate);
  const [femRate, setFemRate] = useState(author.feminine_ending_rate);
  const [homeo, setHomeo] = useState(author.sentence_solaas_homeostasis);
  const [digress, setDigress] = useState(author.compilatio_digression_density);
  const [irony, setIrony] = useState(author.ironic_disclaimer_threshold);

  useEffect(() => {
    setV2Rate(author.v2_topicalization_rate);
    setFemRate(author.feminine_ending_rate);
    setHomeo(author.sentence_solaas_homeostasis);
    setDigress(author.compilatio_digression_density);
    setIrony(author.ironic_disclaimer_threshold);
  }, [author]);

  const calibrateMutation = useMutation({
    mutationFn: async (resetToEmpirical: boolean) => {
      const payload = resetToEmpirical
        ? { reset_to_empirical: true }
        : {
            v2_topicalization_rate: v2Rate,
            feminine_ending_rate: femRate,
            sentence_solaas_homeostasis: homeo,
            compilatio_digression_density: digress,
            ironic_disclaimer_threshold: irony,
          };
      const res = await apiRequest("POST", "/api/calibrate", payload);
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/overview"] });
    },
  });

  return (
    <div className="mx-auto max-w-7xl space-y-5">
      <div className="border-b border-border pb-4">
        <div className="font-mono text-xs font-semibold uppercase tracking-wider text-primary">
          AUTHOR_DEFINITION (FACTORS F1–F6)
        </div>
        <h1 className="mt-0.5 text-xl font-semibold tracking-tight">
          Empirical Chaucer Operator Calibration (Strata S2 &amp; S3)
        </h1>
        <p className="mt-1 max-w-3xl text-xs text-muted-foreground">
          Fitted strictly on non-Canterbury Chaucerian works (Troilus and Criseyde, The Legend of Good Women, Boece) and PPCME2 clause syntax. Adjusting operator parameters updates subsequent turn synthesis in SQLite without touching holdout Stratum S1.
        </p>
      </div>

      {/* Empirical Invariants Strip */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 num-tabular">
        <Card className="border-card-border bg-card shadow-xs">
          <CardContent className="p-3.5">
            <div className="text-xs text-muted-foreground">
              Calibrated S2 Corpus
            </div>
            <div className="mt-1 font-mono text-lg font-semibold">
              {author.total_calibrated_lines} lines / {author.total_calibrated_tokens} tok
            </div>
            <div className="mt-0.5 text-xs text-muted-foreground">
              {author.calibrated_works.length} reference works
            </div>
          </CardContent>
        </Card>

        <Card className="border-card-border bg-card shadow-xs">
          <CardContent className="p-3.5">
            <div className="text-xs text-muted-foreground">
              F1 Romance Content Share
            </div>
            <div className="mt-1 font-mono text-lg font-semibold text-primary">
              {Math.round(author.etymological_rom_gmc_ratio * 100)}%
            </div>
            <div className="mt-0.5 text-xs text-muted-foreground">
              OF + AN + LAT content lemmas
            </div>
          </CardContent>
        </Card>

        <Card className="border-card-border bg-card shadow-xs">
          <CardContent className="p-3.5">
            <div className="text-xs text-muted-foreground">
              F2 Negative Concord Rate
            </div>
            <div className="mt-1 font-mono text-lg font-semibold">
              {Math.round(author.negative_concord_rate * 100)}%
            </div>
            <div className="mt-0.5 text-xs text-muted-foreground">
              Preverbal ne ... nat/noon
            </div>
          </CardContent>
        </Card>

        <Card className="border-card-border bg-card shadow-xs">
          <CardContent className="p-3.5">
            <div className="text-xs text-muted-foreground">
              F3 Sandhi Elision Density
            </div>
            <div className="mt-1 font-mono text-lg font-semibold">
              {author.elision_per_line_rate.toFixed(2)} / line
            </div>
            <div className="mt-0.5 text-xs text-muted-foreground">
              Prevocalic &amp; weak-h -e elisions
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-12">
        {/* Left 6 Cols: Etymology Distribution Chart & S2 Sources */}
        <Card className="border-card-border bg-card shadow-xs lg:col-span-6">
          <CardHeader className="pb-3 pt-4">
            <CardTitle className="text-base font-semibold">
              F1 &middot; Empirical Etymological Distribution (Stratum S2)
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4 pb-4">
            <div className="space-y-3 num-tabular">
              {Object.entries(author.etymology_distribution).map(
                ([etym, share]) => {
                  const pct = Math.round(share * 1000) / 10;
                  return (
                    <div key={etym} className="space-y-1 text-xs">
                      <div className="flex items-center justify-between">
                        <span className="font-medium">
                          {ETYMON_LABELS[etym] || etym}
                        </span>
                        <span className="font-mono font-semibold">{pct}%</span>
                      </div>
                      <div className="h-2.5 w-full overflow-hidden rounded-full bg-secondary">
                        <div
                          className="h-full rounded-full bg-primary transition-all"
                          style={{ width: `${Math.min(100, pct)}%` }}
                        />
                      </div>
                    </div>
                  );
                }
              )}
            </div>

            <div className="rounded-md border border-border bg-background/65 p-3 text-xs">
              <div className="font-semibold text-foreground">
                Calibrated Non-Canterbury Works (Zero S1 Leakage):
              </div>
              <ul className="mt-1.5 space-y-1 text-muted-foreground">
                {author.calibrated_works.map((w, idx) => (
                  <li key={idx} className="flex items-center gap-2">
                    <Badge variant="outline" className="font-mono text-xs">
                      S2.{idx + 1}
                    </Badge>
                    <span className="text-foreground">{w}</span>
                  </li>
                ))}
              </ul>
            </div>
          </CardContent>
        </Card>

        {/* Right 6 Cols: Interactive Operator Parameter Controls */}
        <Card className="border-card-border bg-card shadow-xs lg:col-span-6">
          <CardHeader className="pb-3 pt-4">
            <CardTitle className="flex items-center justify-between text-base font-semibold">
              <span>Interactive Operator Parameters (C)</span>
              <Badge variant="secondary" className="font-mono text-xs">
                {author.dialect_base}
              </Badge>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4 pb-4">
            <SliderRow
              id="slider-v2"
              label="F2 V2 Topicalization & Inversion Rate"
              value={v2Rate}
              min={0.1}
              max={0.9}
              step={0.02}
              onChange={setV2Rate}
              hint="Frequency of fronted adverbial/PP verb-second inversion (Whan/Ther-fore + V_fin + Subj)."
            />
            <SliderRow
              id="slider-fem"
              label="F3 Hendecasyllabic Feminine -e Rate"
              value={femRate}
              min={0.15}
              max={0.8}
              step={0.02}
              onChange={setFemRate}
              hint="Target share of 11-syllable lines ending on unelided etymological or inflectional -e."
            />
            <SliderRow
              id="slider-homeo"
              label="F6 Sentence / Solaas Homeostasis Setpoint"
              value={homeo}
              min={0.15}
              max={0.85}
              step={0.05}
              onChange={setHomeo}
              hint="Lambda_balance equilibrium between moral doctrine (1.0) and festive game (0.0)."
            />
            <SliderRow
              id="slider-digress"
              label="F4 Compilatio Rhetorical Digression Density"
              value={digress}
              min={0.05}
              max={0.55}
              step={0.05}
              onChange={setDigress}
              hint="Probability of inserting apostrophe/sententia digressio in Beat 4."
            />
            <SliderRow
              id="slider-irony"
              label="F5 Reportorial Disclaimer Threshold (K_irony)"
              value={irony}
              min={0.2}
              max={0.9}
              step={0.05}
              onChange={setIrony}
              hint="Threshold at which narrator distances auctoritas from churlish speech."
            />

            <div className="flex flex-wrap items-center justify-between gap-2 pt-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => calibrateMutation.mutate(true)}
                disabled={calibrateMutation.isPending}
                data-testid="restore-empirical-btn"
                className="h-8 gap-1.5 text-xs"
              >
                <RotateCcw className="h-3.5 w-3.5" />
                <span>Restore Empirical S2/S3 Fit</span>
              </Button>

              <Button
                size="sm"
                onClick={() => calibrateMutation.mutate(false)}
                disabled={calibrateMutation.isPending}
                data-testid="save-operator-btn"
                className="h-8 gap-1.5 px-4 text-xs font-semibold"
              >
                <Save className="h-3.5 w-3.5" />
                <span>
                  {calibrateMutation.isPending
                    ? "Updating Operator..."
                    : "Apply Operator Parameters"}
                </span>
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function SliderRow({
  id,
  label,
  value,
  min,
  max,
  step,
  onChange,
  hint,
}: {
  id: string;
  label: string;
  value: number;
  min: number;
  max: number;
  step: number;
  onChange: (v: number) => void;
  hint: string;
}) {
  return (
    <div className="space-y-1 text-xs">
      <div className="flex items-center justify-between">
        <label htmlFor={id} className="font-medium text-foreground">
          {label}
        </label>
        <span className="font-mono font-semibold text-primary num-tabular">
          {Math.round(value * 100)}%
        </span>
      </div>
      <input
        id={id}
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(parseFloat(e.target.value))}
        className="h-2 w-full cursor-pointer accent-primary"
      />
      <p className="text-xs text-muted-foreground">{hint}</p>
    </div>
  );
}
