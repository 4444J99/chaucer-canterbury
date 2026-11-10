import { useEffect, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import {
  ArrowRight,
  CheckCircle2,
  Download,
  Play,
  RotateCcw,
  ShieldAlert,
  Sparkles,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { apiRequest, queryClient } from "@/lib/queryClient";
import {
  GeneratedTurnArtifact,
  StudioOverview,
} from "@/lib/types";

interface GenerativeCorePageProps {
  overview: StudioOverview;
  pendingSpeakerOverride: string | null;
  onConsumeSpeakerOverride: () => void;
}

type ReaderLayer = "normalized" | "hengwrt" | "ellesmere" | "phonology" | "tei";

const FORM_LABELS: Record<string, string> = {
  riding_rhyme_couplet: "Riding Rhyme Couplets (AABB)",
  rhyme_royal_ababbcc: "Rhyme Royal Stanzas (ABABBCC)",
  tail_rhyme_sixain: "Tail-Rhyme Sixain (AABCCB)",
  cadenced_prose: "Cadenced Philosophical Prose",
};

function downloadTextAsset(filename: string, content: string, mime: string) {
  const blob = new Blob([content], { type: mime });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

export function GenerativeCorePage({
  overview,
  pendingSpeakerOverride,
  onConsumeSpeakerOverride,
}: GenerativeCorePageProps) {
  const {
    world_state: world,
    route_segments: segments,
    speaker_probabilities: speakerScores,
    pilgrims,
    source_graphs: sourceGraphs,
    turns,
  } = overview;

  const [selectedTurnId, setSelectedTurnId] = useState<number>(
    turns.length > 0 ? turns[turns.length - 1].turn_id : 1
  );
  const [readerLayer, setReaderLayer] = useState<ReaderLayer>("normalized");
  const [speakerChoice, setSpeakerChoice] = useState<string>("");
  const [sourceChoice, setSourceChoice] = useState<string>("");
  const [formChoice, setFormChoice] = useState<string>("");
  const [unitCount, setUnitCount] = useState<number>(3);

  const generateMutation = useMutation({
    mutationFn: async (overrideSpeaker?: string) => {
      const payload = {
        forced_speaker_id:
          overrideSpeaker !== undefined
            ? overrideSpeaker || null
            : speakerChoice || null,
        forced_source_id: sourceChoice || null,
        forced_form: formChoice || null,
        unit_count: unitCount,
      };
      const res = await apiRequest("POST", "/api/generate-turn", payload);
      return res.json();
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["/api/overview"] });
      if (data?.turn?.turn_id) {
        setSelectedTurnId(data.turn.turn_id);
      }
    },
  });

  const resetMutation = useMutation({
    mutationFn: async () => {
      const res = await apiRequest("POST", "/api/world/reset", {});
      return res.json();
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["/api/overview"] });
      if (data?.turns?.[0]?.turn_id) {
        setSelectedTurnId(data.turns[0].turn_id);
      }
    },
  });

  useEffect(() => {
    if (pendingSpeakerOverride) {
      setSpeakerChoice(pendingSpeakerOverride);
      generateMutation.mutate(pendingSpeakerOverride);
      onConsumeSpeakerOverride();
    }
  }, [pendingSpeakerOverride]);

  const activeTurn: GeneratedTurnArtifact | undefined =
    turns.find((t) => t.turn_id === selectedTurnId) || turns[turns.length - 1];

  const silentPilgrims = pilgrims.filter(
    (p) => p.manuscript_status.includes("silent") && p.id !== "harry_bailly"
  );
  const extantPilgrims = pilgrims.filter(
    (p) => !p.manuscript_status.includes("silent") && p.id !== "harry_bailly"
  );

  return (
    <div className="mx-auto max-w-7xl space-y-5">
      {/* Page Title & Protocol Summary */}
      <div className="flex flex-col justify-between gap-3 border-b border-border pb-4 sm:flex-row sm:items-end">
        <div>
          <div className="font-mono text-xs font-semibold uppercase tracking-wider text-primary">
            GENERATIVE_CORE + WORLD_STATE
          </div>
          <h1 className="mt-0.5 text-xl font-semibold tracking-tight">
            Protocol-Bound Pilgrimage &amp; Multi-Witness Tale Synthesis
          </h1>
          <p className="mt-1 max-w-3xl text-xs text-muted-foreground">
            Executes the five-stage generative pipeline strictly isolated from Stratum S1 witnesses: Host scheduling and quiting interruptions, pre-1400 S5 compilatio beat transposition, sociolect conditioning, and WFST-screened Middle English scansion.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => resetMutation.mutate()}
            disabled={resetMutation.isPending || generateMutation.isPending}
            data-testid="reset-road-btn"
            className="h-8 gap-1.5 text-xs"
          >
            <RotateCcw className="h-3.5 w-3.5" />
            <span>Reset Tabard Departure</span>
          </Button>
        </div>
      </div>

      {/* Kentish Road Itinerary & Homeostasis Bar */}
      <Card className="border-card-border bg-card shadow-xs">
        <CardContent className="p-4">
          <div className="flex flex-wrap items-center justify-between gap-3 pb-3">
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Kentish Road Itinerary
              </span>
              <Badge variant="secondary" className="font-mono text-xs num-tabular">
                {world.time_of_day}
              </Badge>
            </div>
            <div className="flex flex-wrap items-center gap-4 text-xs num-tabular">
              <div>
                <span className="text-muted-foreground">Host Patience: </span>
                <span className="font-mono font-semibold">
                  {Math.round(world.host_patience * 100)}%
                </span>
              </div>
              <div>
                <span className="text-muted-foreground">Sentence / Solaas Balance: </span>
                <span className="font-mono font-semibold text-primary">
                  {Math.round(world.rolling_sentence_level * 100)}%
                </span>
                <span className="text-muted-foreground"> / </span>
                <span className="font-mono font-semibold">
                  {Math.round(world.rolling_solaas_level * 100)}%
                </span>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-1.5 sm:grid-cols-5 lg:grid-cols-10">
            {segments.map((seg, idx) => {
              const isCurrent = idx === world.route_stage_index;
              const isPassed = idx < world.route_stage_index;
              return (
                <div
                  key={seg.stage_index}
                  className={`rounded border px-2 py-1.5 text-xs transition-colors ${
                    isCurrent
                      ? "border-primary bg-primary/10 text-foreground"
                      : isPassed
                      ? "border-border bg-secondary/60 text-foreground"
                      : "border-border/60 bg-background/50 text-muted-foreground"
                  }`}
                >
                  <div className="flex items-center justify-between font-mono text-xs num-tabular">
                    <span>M{seg.mile}</span>
                    {isCurrent && (
                      <span className="h-1.5 w-1.5 rounded-full bg-primary" />
                    )}
                  </div>
                  <div className="mt-0.5 truncate font-medium" title={seg.name}>
                    {seg.name.split("—")[0].trim()}
                  </div>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Top Grid: Synthesis Controller + Next Speaker Probability Matrix */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-12">
        <Card className="border-card-border bg-card shadow-xs lg:col-span-7">
          <CardHeader className="pb-3 pt-4">
            <CardTitle className="flex items-center justify-between text-base font-semibold">
              <span>Stage 1–5 Synthesis Dispatch</span>
              <span className="font-mono text-xs font-normal text-muted-foreground">
                {speakerChoice ? "Mode: Researcher Override" : "Mode: Autonomous Frame Protocol"}
              </span>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3.5 pb-4">
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <div>
                <label
                  htmlFor="speaker-select"
                  className="mb-1 block text-xs font-medium text-muted-foreground"
                >
                  Pilgrim Speaker (30 General Prologue Agents)
                </label>
                <select
                  id="speaker-select"
                  value={speakerChoice}
                  onChange={(e) => setSpeakerChoice(e.target.value)}
                  data-testid="speaker-select"
                  className="h-9 w-full rounded-md border border-input bg-background px-2.5 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-ring"
                >
                  <option value="">
                    Autonomous (Harry Bailly + Quiting Ledger)
                  </option>
                  <optgroup label="7 Historically Silent General Prologue Pilgrims">
                    {silentPilgrims.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.name} — {p.role_title} [Silent in MS]
                      </option>
                    ))}
                  </optgroup>
                  <optgroup label="22 Extant General Prologue Tale-Tellers">
                    {extantPilgrims.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.name} — {p.role_title}
                      </option>
                    ))}
                  </optgroup>
                </select>
              </div>

              <div>
                <label
                  htmlFor="form-select"
                  className="mb-1 block text-xs font-medium text-muted-foreground"
                >
                  Metrical or Prose Vehicle
                </label>
                <select
                  id="form-select"
                  value={formChoice}
                  onChange={(e) => setFormChoice(e.target.value)}
                  data-testid="form-select"
                  className="h-9 w-full rounded-md border border-input bg-background px-2.5 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-ring"
                >
                  <option value="">Auto-Conditioned by Pilgrim Competence</option>
                  <option value="riding_rhyme_couplet">
                    Riding Rhyme Couplet (AABB Decasyllabic)
                  </option>
                  <option value="rhyme_royal_ababbcc">
                    Rhyme Royal Stanza (ABABBCC)
                  </option>
                  <option value="tail_rhyme_sixain">
                    Tail-Rhyme Sixain (AABCCB Burlesque)
                  </option>
                  <option value="cadenced_prose">
                    Cadenced Philosophical Prose
                  </option>
                </select>
              </div>

              <div>
                <label
                  htmlFor="source-select"
                  className="mb-1 block text-xs font-medium text-muted-foreground"
                >
                  Pre-1400 S5 Compilatio Substrate
                </label>
                <select
                  id="source-select"
                  value={sourceChoice}
                  onChange={(e) => setSourceChoice(e.target.value)}
                  data-testid="source-select"
                  className="h-9 w-full rounded-md border border-input bg-background px-2.5 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-ring"
                >
                  <option value="">
                    Auto-Scored (Affinity + QuitingContrast + Homeostasis)
                  </option>
                  {sourceGraphs.map((sg) => (
                    <option key={sg.source_id} value={sg.source_id}>
                      {sg.title} ({sg.auctor}, {sg.year_composed} CE)
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label
                  htmlFor="unit-select"
                  className="mb-1 block text-xs font-medium text-muted-foreground"
                >
                  Stanza / Couplet Block Depth
                </label>
                <select
                  id="unit-select"
                  value={unitCount}
                  onChange={(e) => setUnitCount(Number(e.target.value))}
                  className="h-9 w-full rounded-md border border-input bg-background px-2.5 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-ring"
                >
                  <option value={2}>Compact (2 Stanzas / 4 Couplets)</option>
                  <option value={3}>Standard (3 Stanzas / 6 Couplets)</option>
                  <option value={4}>Extended (3 Stanzas / 8 Couplets)</option>
                </select>
              </div>
            </div>

            <div className="flex flex-wrap items-center justify-between gap-2 pt-1">
              <div className="flex flex-wrap gap-1.5">
                <Button
                  type="button"
                  variant="secondary"
                  size="sm"
                  className="h-7 text-xs"
                  onClick={() => {
                    setSpeakerChoice("plowman");
                    setFormChoice("riding_rhyme_couplet");
                  }}
                >
                  Preset: Silent Plowman
                </Button>
                <Button
                  type="button"
                  variant="secondary"
                  size="sm"
                  className="h-7 text-xs"
                  onClick={() => {
                    setSpeakerChoice("carpenter");
                    setFormChoice("riding_rhyme_couplet");
                  }}
                >
                  Preset: Silent Guild Carpenter
                </Button>
                <Button
                  type="button"
                  variant="secondary"
                  size="sm"
                  className="h-7 text-xs"
                  onClick={() => {
                    setSpeakerChoice("clerk");
                    setFormChoice("rhyme_royal_ababbcc");
                  }}
                >
                  Preset: Clerk Rhyme Royal
                </Button>
              </div>

              <Button
                onClick={() => generateMutation.mutate(undefined)}
                disabled={generateMutation.isPending}
                data-testid="generate-turn-btn"
                className="h-9 gap-1.5 px-4 text-xs font-semibold"
              >
                <Play className="h-3.5 w-3.5" />
                <span>
                  {generateMutation.isPending
                    ? "Synthesizing & Scanning..."
                    : `Synthesize Turn ${world.turn_index + 1}`}
                </span>
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Next Speaker Probability & Quiting Tension Card */}
        <Card className="border-card-border bg-card shadow-xs lg:col-span-5">
          <CardHeader className="pb-2 pt-4">
            <CardTitle className="flex items-center justify-between text-base font-semibold">
              <span>Next Speaker Distribution P(p_t | W_t)</span>
              <span className="font-mono text-xs font-normal text-muted-foreground num-tabular">
                Top 5 of 29
              </span>
            </CardTitle>
          </CardHeader>
          <CardContent className="pb-4">
            <div className="space-y-2">
              {speakerScores.slice(0, 5).map((sc) => (
                <div
                  key={sc.pilgrim_id}
                  className="flex items-center justify-between gap-2 rounded border border-border/70 bg-background/60 px-2.5 py-1.5 text-xs"
                >
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-1.5">
                      <span className="truncate font-medium">
                        {sc.pilgrim_name}
                      </span>
                      {sc.would_interrupt && (
                        <Badge
                          variant="default"
                          className="h-4 px-1.5 font-mono text-xs"
                        >
                          QUITING INTERRUPT
                        </Badge>
                      )}
                    </div>
                    <div className="mt-0.5 font-mono text-xs text-muted-foreground num-tabular">
                      Host {sc.host_call_score.toFixed(2)} &middot; Grievance{" "}
                      {sc.grievance_drive.toFixed(2)}
                    </div>
                  </div>
                  <div className="text-right font-mono text-xs font-semibold num-tabular">
                    {(sc.probability * 100).toFixed(1)}%
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Turn History Tabs */}
      <div className="flex flex-wrap items-center gap-1.5 border-b border-border pb-3">
        <span className="mr-1 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          Emitted Turns:
        </span>
        {turns.map((t) => {
          const isSelected = activeTurn?.turn_id === t.turn_id;
          return (
            <button
              key={t.turn_id}
              type="button"
              onClick={() => setSelectedTurnId(t.turn_id)}
              data-testid={`turn-tab-${t.turn_id}`}
              className={`inline-flex items-center gap-1.5 rounded-md border px-3 py-1.5 text-xs font-medium transition-colors num-tabular ${
                isSelected
                  ? "border-primary bg-primary text-primary-foreground"
                  : "border-border bg-card text-foreground hover:bg-secondary"
              }`}
            >
              <span className="font-mono">T{t.turn_index}</span>
              <span>{t.speaker_name}</span>
              {t.manuscript_status.includes("silent") && (
                <span
                  className={`rounded px-1 font-mono text-xs ${
                    isSelected
                      ? "bg-primary-foreground/20 text-primary-foreground"
                      : "bg-primary/12 text-primary"
                  }`}
                >
                  SILENT MS
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Main Artifact Display */}
      {activeTurn && (
        <div className="grid grid-cols-1 gap-5 lg:grid-cols-12">
          {/* Left 8 Cols: Critical Witness & Scansion Reader */}
          <div className="space-y-4 lg:col-span-8">
            <Card className="border-card-border bg-card shadow-xs">
              <CardHeader className="space-y-3 border-b border-border pb-3.5 pt-4">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <Badge variant="outline" className="font-mono text-xs num-tabular">
                        Turn {activeTurn.turn_index} &middot; Mile {activeTurn.mile_marker}
                      </Badge>
                      <Badge variant="secondary" className="font-mono text-xs">
                        {activeTurn.selection_mode}
                      </Badge>
                      {activeTurn.manuscript_status.includes("silent") && (
                        <Badge className="bg-primary text-primary-foreground text-xs">
                          Reconstructed Silent Pilgrim Voice
                        </Badge>
                      )}
                    </div>
                    <h2 className="mt-2 text-lg font-semibold tracking-tight">
                      {activeTurn.speaker_name} ({activeTurn.speaker_role})
                    </h2>
                    <div className="mt-0.5 text-xs text-muted-foreground">
                      Compilatio Source:{" "}
                      <span className="font-medium text-foreground">
                        {activeTurn.source_title}
                      </span>{" "}
                      ({activeTurn.source_auctor}, {activeTurn.source_year} CE) &middot;{" "}
                      {FORM_LABELS[activeTurn.metrical_form] || activeTurn.metrical_form}
                    </div>
                  </div>

                  <div className="flex items-center gap-1.5">
                    <Button
                      variant="outline"
                      size="sm"
                      className="h-8 gap-1.5 text-xs"
                      data-testid="download-tei-btn"
                      onClick={() =>
                        downloadTextAsset(
                          `turn_${activeTurn.turn_index}_${activeTurn.speaker_id}_apparatus.xml`,
                          activeTurn.tei_xml_apparatus,
                          "application/xml"
                        )
                      }
                    >
                      <Download className="h-3.5 w-3.5" />
                      <span>TEI-XML</span>
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      className="h-8 gap-1.5 text-xs"
                      data-testid="download-json-btn"
                      onClick={() =>
                        downloadTextAsset(
                          `turn_${activeTurn.turn_index}_${activeTurn.speaker_id}_artifact.json`,
                          JSON.stringify(activeTurn, null, 2),
                          "application/json"
                        )
                      }
                    >
                      <Download className="h-3.5 w-3.5" />
                      <span>JSON</span>
                    </Button>
                  </div>
                </div>

                {/* Witness / Orthography Layer Selector */}
                <div className="flex flex-wrap gap-1.5 pt-1">
                  {(
                    [
                      ["normalized", "Normalized 1390 + Gloss"],
                      ["hengwrt", "Hengwrt Witness (Hg, c. 1400)"],
                      ["ellesmere", "Ellesmere Witness (El, c. 1405)"],
                      ["phonology", "IPA + Sandhi & Stress Scan"],
                      ["tei", "TEI-XML Critical Apparatus"],
                    ] as [ReaderLayer, string][]
                  ).map(([key, label]) => (
                    <button
                      key={key}
                      type="button"
                      onClick={() => setReaderLayer(key)}
                      data-testid={`layer-${key}`}
                      className={`rounded border px-2.5 py-1 text-xs font-medium transition-colors ${
                        readerLayer === key
                          ? "border-primary bg-primary/12 text-primary"
                          : "border-border bg-background text-muted-foreground hover:text-foreground"
                      }`}
                    >
                      {label}
                    </button>
                  ))}
                </div>
              </CardHeader>

              <CardContent className="space-y-5 p-4 sm:p-5">
                {readerLayer === "tei" ? (
                  <div>
                    <div className="mb-2 text-xs text-muted-foreground">
                      Parallel Hengwrt (#Hg) and Ellesmere (#El) apparatus criticus encoded in TEI P5 XML:
                    </div>
                    <pre className="max-h-[520px] overflow-auto rounded-md border border-border bg-background p-3.5 font-mono text-xs leading-relaxed text-foreground">
                      {activeTurn.tei_xml_apparatus}
                    </pre>
                  </div>
                ) : (
                  <>
                    {/* Stage 1 Dramatic Link Couplets */}
                    <div>
                      <div className="mb-2.5 flex items-center justify-between border-b border-border/70 pb-1.5">
                        <span className="font-mono text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                          Stage 1 &middot; Frame Link Prologue (Harry Bailly &amp; {activeTurn.speaker_name})
                        </span>
                        <span className="font-mono text-xs text-muted-foreground">
                          Lines 1–{activeTurn.link_lines.length}
                        </span>
                      </div>
                      <div className="space-y-2.5">
                        {activeTurn.link_lines.map((ln) => (
                          <VerseLineRow
                            key={`link-${ln.line_number}`}
                            line={ln}
                            layer={readerLayer}
                          />
                        ))}
                      </div>
                    </div>

                    {/* Ellesmere Latin Marginalia Callout when in Ellesmere mode */}
                    {readerLayer === "ellesmere" && (
                      <div className="rounded-md border border-primary/35 bg-primary/5 p-3">
                        <div className="font-mono text-xs font-semibold uppercase tracking-wider text-primary">
                          Rubricated Ellesmere Latin Marginalia
                        </div>
                        <ul className="mt-1.5 space-y-1 font-serif text-xs text-foreground">
                          {activeTurn.ellesmere_marginalia.map((m, idx) => (
                            <li key={idx}>&para; {m.trim()}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Stage 3 & 4 Tale Body */}
                    <div>
                      <div className="mb-2.5 flex items-center justify-between border-b border-border/70 pb-1.5">
                        <span className="font-mono text-xs font-semibold uppercase tracking-wider text-primary">
                          Stage 3–4 &middot; Synthesized Tale Text ({FORM_LABELS[activeTurn.metrical_form]})
                        </span>
                        <span className="font-mono text-xs text-muted-foreground num-tabular">
                          {activeTurn.tale_lines.length} lines
                        </span>
                      </div>
                      <div className="space-y-2.5">
                        {activeTurn.tale_lines.map((ln) => (
                          <VerseLineRow
                            key={`tale-${ln.line_number}`}
                            line={ln}
                            layer={readerLayer}
                          />
                        ))}
                      </div>
                    </div>
                  </>
                )}
              </CardContent>
            </Card>

            {/* Stage 2 Compilatio Beat Graph */}
            <Card className="border-card-border bg-card shadow-xs">
              <CardHeader className="pb-2.5 pt-4">
                <CardTitle className="text-base font-semibold">
                  Stage 2 &middot; Transposed Compilatio Beat Plan (K_comp)
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2.5 pb-4">
                {activeTurn.beat_plan.map((beat, i) => (
                  <div
                    key={beat.beat_id}
                    className="rounded-md border border-border bg-background/65 p-3 text-xs"
                  >
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <span className="font-mono font-semibold text-primary num-tabular">
                          B{i + 1}
                        </span>
                        <span className="font-semibold uppercase tracking-wide">
                          {beat.role}
                        </span>
                        <Badge variant="secondary" className="font-mono text-xs">
                          {beat.rhetorical_operation}
                        </Badge>
                      </div>
                      <Badge
                        variant="outline"
                        className="font-mono text-xs uppercase"
                      >
                        edge: {beat.causal_edge}
                      </Badge>
                    </div>
                    <p className="mt-1.5 leading-relaxed text-foreground">
                      {beat.adapted_proposition}
                    </p>
                    <div className="mt-1.5 flex flex-wrap items-center gap-1.5">
                      <span className="text-muted-foreground">Focus Lexicon:</span>
                      {beat.focus_lexicon.map((lx) => (
                        <span
                          key={lx}
                          className="rounded border border-border bg-card px-1.5 py-0.5 font-mono text-xs"
                        >
                          {lx}
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>

          {/* Right 4 Cols: Conservation Laws L1-L7, Analytics, Estate Reception & Quiting Matrix */}
          <div className="space-y-4 lg:col-span-4">
            {/* Hard Conservation Laws L1-L7 */}
            <Card className="border-card-border bg-card shadow-xs">
              <CardHeader className="pb-2.5 pt-4">
                <CardTitle className="flex items-center justify-between text-base font-semibold">
                  <span>Conservation Laws (L1–L7)</span>
                  <Badge className="bg-primary text-primary-foreground font-mono text-xs num-tabular">
                    {activeTurn.conservation_laws.filter((c) => c.passed).length}/
                    {activeTurn.conservation_laws.length} Passed
                  </Badge>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 pb-4">
                {activeTurn.conservation_laws.map((law) => (
                  <div
                    key={law.law_id}
                    className="rounded border border-border bg-background/60 p-2.5 text-xs"
                  >
                    <div className="flex items-center justify-between gap-2">
                      <div className="flex items-center gap-1.5 font-semibold">
                        {law.passed ? (
                          <CheckCircle2 className="h-3.5 w-3.5 shrink-0 text-emerald-700 dark:text-emerald-400" />
                        ) : (
                          <ShieldAlert className="h-3.5 w-3.5 shrink-0 text-destructive" />
                        )}
                        <span className="font-mono">{law.law_id}</span>
                        <span>{law.name}</span>
                      </div>
                    </div>
                    <div className="mt-1 flex items-center justify-between font-mono text-xs text-muted-foreground num-tabular">
                      <span>{law.metric_label}</span>
                      <span className="font-semibold text-foreground">
                        {law.metric_value}
                      </span>
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>

            {/* Multi-Scale Diagnostics (LingFrame + Narratology + Vox) */}
            <Card className="border-card-border bg-card shadow-xs">
              <CardHeader className="pb-2.5 pt-4">
                <CardTitle className="text-base font-semibold">
                  Analytical Diagnostics
                </CardTitle>
              </CardHeader>
              <CardContent className="grid grid-cols-2 gap-2 pb-4 text-xs num-tabular">
                <MetricTile
                  label="WFST Scansion Pass"
                  value={`${Math.round(activeTurn.diagnostics.prosody_pass_rate * 100)}%`}
                />
                <MetricTile
                  label="Rhyme Purity"
                  value={`${Math.round(activeTurn.diagnostics.rhyme_purity_rate * 100)}%`}
                />
                <MetricTile
                  label="Romance / Total Ratio"
                  value={`${Math.round(activeTurn.diagnostics.romance_to_germanic_ratio * 100)}%`}
                />
                <MetricTile
                  label="KL Div vs S2"
                  value={activeTurn.diagnostics.kl_divergence_vs_s2.toFixed(3)}
                />
                <MetricTile
                  label="Vox Sociolect Fit"
                  value={`${Math.round(activeTurn.diagnostics.vox_idiolect_alignment * 100)}%`}
                />
                <MetricTile
                  label="Max S1/S2 Similarity"
                  value={activeTurn.diagnostics.max_line_levenshtein_s1_s2.toFixed(2)}
                />
              </CardContent>
            </Card>

            {/* Stage 5 Divergent Estate Reception (L7) */}
            <Card className="border-card-border bg-card shadow-xs">
              <CardHeader className="pb-2.5 pt-4">
                <CardTitle className="text-base font-semibold">
                  Stage 5 &middot; Estate Reception (Law L7)
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2.5 pb-4 text-xs">
                {activeTurn.estate_reactions.map((rx, idx) => (
                  <div
                    key={idx}
                    className="rounded border border-border bg-background/60 p-2.5"
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span className="font-semibold">
                        {rx.representative_pilgrim}
                      </span>
                      <Badge variant="outline" className="font-mono text-xs">
                        {rx.polarity} ({rx.quiting_delta >= 0 ? "+" : ""}
                        {rx.quiting_delta.toFixed(2)})
                      </Badge>
                    </div>
                    <div className="mt-0.5 text-xs text-muted-foreground">
                      {rx.estate_group}
                    </div>
                    <p className="mt-1 leading-relaxed text-foreground">
                      {rx.reaction_summary}
                    </p>
                  </div>
                ))}
                <div className="rounded border border-primary/30 bg-primary/5 p-2.5 text-xs leading-relaxed">
                  <span className="font-semibold text-primary">
                    Harry Bailly Arbitrage:{" "}
                  </span>
                  {activeTurn.host_verdict}
                </div>
              </CardContent>
            </Card>

            {/* Active Quiting Grievance Ledger */}
            <Card className="border-card-border bg-card shadow-xs">
              <CardHeader className="pb-2.5 pt-4">
                <CardTitle className="text-base font-semibold">
                  Directed Quiting Ledger (G_t)
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 pb-4 text-xs">
                {world.quiting_edges.slice(0, 6).map((edge, idx) => (
                  <div
                    key={`${edge.source_pilgrim}-${edge.target_pilgrim}-${idx}`}
                    className="rounded border border-border bg-background/60 px-2.5 py-2"
                  >
                    <div className="flex items-center justify-between font-mono text-xs num-tabular">
                      <span className="flex items-center gap-1 font-semibold text-foreground">
                        <span>{edge.source_pilgrim}</span>
                        <ArrowRight className="h-3 w-3 text-primary" />
                        <span>{edge.target_pilgrim}</span>
                      </span>
                      <span className="font-semibold text-primary">
                        w={edge.weight.toFixed(2)}
                      </span>
                    </div>
                    <div className="mt-0.5 text-xs text-muted-foreground">
                      {edge.reason}
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>
        </div>
      )}
    </div>
  );
}

function VerseLineRow({
  line,
  layer,
}: {
  line: GeneratedTurnArtifact["tale_lines"][number];
  layer: Exclude<ReaderLayer, "tei">;
}) {
  const primaryText =
    layer === "hengwrt"
      ? line.hengwrt_orthography
      : layer === "ellesmere"
      ? line.ellesmere_orthography
      : line.middle_english;

  return (
    <div className="rounded-md border border-border/75 bg-background/70 px-3 py-2">
      <div className="flex items-baseline justify-between gap-3">
        <div className="flex items-baseline gap-2.5">
          <span className="w-6 shrink-0 select-none font-mono text-xs text-muted-foreground num-tabular">
            {line.line_number}
          </span>
          <span className="font-serif text-base font-medium leading-snug text-foreground">
            {primaryText}
          </span>
        </div>
        <span className="shrink-0 font-mono text-xs text-primary num-tabular">
          /{line.rhyme_key}/
        </span>
      </div>

      {layer === "phonology" ? (
        <div className="mt-1.5 pl-8 space-y-1 font-mono text-xs">
          <div className="text-foreground">[{line.ipa_transcription}]</div>
          <div className="flex flex-wrap items-center gap-2 text-muted-foreground num-tabular">
            <span>Pattern: {line.metrical_pattern}</span>
            <span>&middot;</span>
            <span>{line.syllable_count} sylls</span>
            <span>&middot;</span>
            <span>License: {line.license_used}</span>
            {line.elision_events.length > 0 && (
              <span className="rounded bg-primary/10 px-1.5 py-0.5 text-primary">
                Sandhi: {line.elision_events.join(", ")}
              </span>
            )}
          </div>
        </div>
      ) : (
        <div className="mt-1 pl-8 text-xs text-muted-foreground">
          {line.modern_gloss}
        </div>
      )}
    </div>
  );
}

function MetricTile({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded border border-border bg-background/60 px-2.5 py-2">
      <div className="text-xs text-muted-foreground">{label}</div>
      <div className="mt-0.5 font-mono text-sm font-semibold text-foreground num-tabular">
        {value}
      </div>
    </div>
  );
}
