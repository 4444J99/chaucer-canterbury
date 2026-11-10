import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { CheckCircle2, Play, XCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { apiRequest } from "@/lib/queryClient";
import { CorpusAuditReport, ScanWorkbenchResponse } from "@/lib/types";

const PRESETS = [
  {
    id: "troilus_proem",
    label: "Troilus Book I Proem (Rhyme Royal ABABBCC)",
    scheme: "ABABBCC",
    text: [
      "The double sorwe of Troilus to tellen,",
      "That was the kyng Priamus sone of Troye,",
      "In lovynge, how his aventures fellen",
      "Fro wo to wele, and after out of joie,",
      "My purpos is, er that I parte fro ye.",
      "Thesiphone, thow help me for tendite",
      "Thise woful vers, that wepen as I write.",
    ].join("\n"),
  },
  {
    id: "lgw_couplets",
    label: "Legend of Good Women Prologue (Couplets AABB)",
    scheme: "AABB",
    text: [
      "A thousand tymes have I herd men telle",
      "That ther ys joy in hevene and peyne in helle,",
      "And I acorde wel that it ys so;",
      "But, natheles, yet wot I wel also,",
    ].join("\n"),
  },
  {
    id: "sandhi_elision",
    label: "Final -e Prevocalic & Weak-h Sandhi",
    scheme: "AABB",
    text: [
      "With sad visage and humble herte in grace,",
      "Ther nas no wight that knew so trewe a place.",
    ].join("\n"),
  },
  {
    id: "adversarial_vowel",
    label: "Adversarial: Open /ɔː/ vs Close /oː/ Rhyme Reject",
    scheme: "AABB",
    text: [
      "And forth they riden in good entente to goon,",
      "By Goddes might this trewe dede is doon.",
    ].join("\n"),
  },
  {
    id: "adversarial_l1",
    label: "Adversarial: Law L1 Post-1400 Anachronism Reject",
    scheme: "SINGLE",
    text: "Whan disillusion cometh to our place,",
  },
];

export function PhonologyWorkbenchPage() {
  const [inputText, setInputText] = useState<string>(PRESETS[0].text);
  const [scheme, setScheme] = useState<string>(PRESETS[0].scheme);
  const [auditWork, setAuditWork] = useState<"troilus" | "lgw">("troilus");

  const scanMutation = useMutation({
    mutationFn: async (vars: { text: string; rhyme_scheme: string }) => {
      const res = await apiRequest("POST", "/api/scan", vars);
      return (await res.json()) as ScanWorkbenchResponse;
    },
  });

  const initialScanQuery = useQuery<ScanWorkbenchResponse>({
    queryKey: ["/api/scan/initial-troilus"],
    queryFn: async () => {
      const res = await apiRequest("POST", "/api/scan", {
        text: PRESETS[0].text,
        rhyme_scheme: PRESETS[0].scheme,
      });
      return res.json();
    },
  });

  const corpusAuditQuery = useQuery<CorpusAuditReport>({
    queryKey: [`/api/corpus-audit/${auditWork}`],
  });

  const activeScan = scanMutation.data ?? initialScanQuery.data;

  const applyPreset = (preset: (typeof PRESETS)[number]) => {
    setInputText(preset.text);
    setScheme(preset.scheme);
    scanMutation.mutate({ text: preset.text, rhyme_scheme: preset.scheme });
  };

  return (
    <div className="mx-auto max-w-7xl space-y-5">
      <div className="border-b border-border pb-4">
        <div className="font-mono text-xs font-semibold uppercase tracking-wider text-primary">
          PHONOLOGY_WORKBENCH (STRATUM S4 + LAWS L1 &amp; L4)
        </div>
        <h1 className="mt-0.5 text-xl font-semibold tracking-tight">
          Middle English Phonological Transcriber &amp; Final -e Scansion Validator
        </h1>
        <p className="mt-1 max-w-3xl text-xs text-muted-foreground">
          Deterministic pre-Great-Vowel-Shift London IPA transducer, prevocalic and weak-h final -e sandhi resolver, open versus close mid-vowel rhyme discriminator, and WFST pentameter aligner.
        </p>
      </div>

      {/* Interactive Workbench Input */}
      <Card className="border-card-border bg-card shadow-xs">
        <CardHeader className="pb-3 pt-4">
          <CardTitle className="flex flex-wrap items-center justify-between gap-2 text-base font-semibold">
            <span>Interactive Line &amp; Stanza Scansion Input</span>
            <div className="flex flex-wrap gap-1.5">
              {PRESETS.map((p) => (
                <button
                  key={p.id}
                  type="button"
                  onClick={() => applyPreset(p)}
                  data-testid={`preset-${p.id}`}
                  className="rounded border border-border bg-background px-2 py-1 text-xs font-medium text-foreground hover:bg-secondary"
                >
                  {p.label.split("(")[0].trim()}
                </button>
              ))}
            </div>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 pb-4">
          <textarea
            rows={8}
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            data-testid="phonology-textarea"
            className="w-full rounded-md border border-input bg-background p-3 font-serif text-base leading-relaxed text-foreground focus:outline-none focus:ring-1 focus:ring-ring"
            placeholder="Enter Middle English verse lines..."
          />

          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <label
                htmlFor="scheme-select"
                className="text-xs font-medium text-muted-foreground"
              >
                Stanza / Rhyme Audit Mode:
              </label>
              <select
                id="scheme-select"
                value={scheme}
                onChange={(e) => setScheme(e.target.value)}
                data-testid="scheme-select"
                className="h-8 rounded-md border border-input bg-background px-2.5 text-xs text-foreground"
              >
                <option value="SINGLE">Line-by-Line Pentameter Only</option>
                <option value="AABB">Riding Rhyme Couplets (AABB...)</option>
                <option value="ABABBCC">Rhyme Royal Stanza (7 lines ABABBCC)</option>
              </select>
            </div>

            <Button
              size="sm"
              onClick={() =>
                scanMutation.mutate({ text: inputText, rhyme_scheme: scheme })
              }
              disabled={scanMutation.isPending}
              data-testid="run-scan-btn"
              className="h-8 gap-1.5 px-4 text-xs font-semibold"
            >
              <Play className="h-3.5 w-3.5" />
              <span>
                {scanMutation.isPending
                  ? "Transcribing..."
                  : "Transcribe & Validate Scansion"}
              </span>
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Scansion Results */}
      {activeScan && (
        <div className="space-y-4">
          {activeScan.stanza_audit && (
            <Card className="border-card-border bg-card shadow-xs">
              <CardHeader className="pb-2.5 pt-4">
                <CardTitle className="flex flex-wrap items-center justify-between gap-2 text-base font-semibold">
                  <span>
                    Stanza Rhyme &amp; Vowel-Quality Audit (
                    {activeScan.stanza_audit.rhyme_scheme})
                  </span>
                  <Badge
                    variant={
                      activeScan.stanza_audit.is_valid ? "default" : "destructive"
                    }
                    className="font-mono text-xs num-tabular"
                  >
                    {activeScan.stanza_audit.is_valid
                      ? "STANZA VALID"
                      : "STANZA VIOLATION DETECTED"}
                  </Badge>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 pb-4">
                <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
                  {activeScan.stanza_audit.rhyme_audits.map((ra) => (
                    <div
                      key={ra.label}
                      className="rounded border border-border bg-background/70 p-2.5 text-xs"
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-mono font-semibold">
                          Band {ra.label} (Lines {ra.line_numbers.join(", ")})
                        </span>
                        {ra.is_valid ? (
                          <CheckCircle2 className="h-4 w-4 text-emerald-700 dark:text-emerald-400" />
                        ) : (
                          <XCircle className="h-4 w-4 text-destructive" />
                        )}
                      </div>
                      <div className="mt-1 font-serif text-sm font-medium">
                        {ra.end_words.join(" / ")}
                      </div>
                      <div className="mt-0.5 font-mono text-xs text-muted-foreground">
                        Keys: {ra.rhyme_keys.map((k) => `/${k}/`).join(" vs ")}{" "}
                        &middot; {ra.status}
                      </div>
                    </div>
                  ))}
                </div>

                {activeScan.stanza_audit.violations.length > 0 && (
                  <div className="rounded border border-destructive/40 bg-destructive/10 p-3 text-xs text-destructive">
                    <div className="font-semibold">Phonological &amp; Metrical Rejections:</div>
                    <ul className="mt-1 list-disc pl-4 space-y-0.5">
                      {activeScan.stanza_audit.violations.map((v, i) => (
                        <li key={i}>{v}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* Line-by-Line Token & Sandhi Cards */}
          <div className="space-y-3">
            {activeScan.lines.map((ln, idx) => {
              const profiles = activeScan.word_profiles[idx] || [];
              return (
                <Card
                  key={ln.line_number}
                  className="border-card-border bg-card shadow-xs"
                >
                  <CardContent className="space-y-3 p-4">
                    <div className="flex flex-wrap items-start justify-between gap-2">
                      <div>
                        <div className="flex items-center gap-2">
                          {ln.is_valid ? (
                            <CheckCircle2 className="h-4 w-4 text-emerald-700 dark:text-emerald-400" />
                          ) : (
                            <XCircle className="h-4 w-4 text-destructive" />
                          )}
                          <span className="font-mono text-xs text-muted-foreground num-tabular">
                            Line {ln.line_number}
                          </span>
                          <span className="font-serif text-base font-semibold">
                            {ln.original_text}
                          </span>
                        </div>
                        {ln.ipa_transcription && (
                          <div className="mt-1 pl-6 font-mono text-xs text-muted-foreground">
                            IPA: [{ln.ipa_transcription}]
                          </div>
                        )}
                      </div>

                      <div className="flex flex-wrap items-center gap-1.5 font-mono text-xs num-tabular">
                        <Badge variant="outline">
                          {ln.metrical_pattern || "unaligned"}
                        </Badge>
                        <Badge variant="secondary">
                          {ln.syllable_count} sylls
                        </Badge>
                        {ln.license_used && (
                          <Badge variant="secondary">{ln.license_used}</Badge>
                        )}
                        {ln.rhyme_key && (
                          <Badge className="bg-primary text-primary-foreground">
                            /{ln.rhyme_key}/
                          </Badge>
                        )}
                      </div>
                    </div>

                    {ln.l1_violations.length > 0 && (
                      <div className="rounded border border-destructive/40 bg-destructive/10 px-3 py-2 text-xs text-destructive">
                        {ln.l1_violations.join(" | ")}
                      </div>
                    )}
                    {!ln.is_valid && ln.l4_notes.length > 0 && (
                      <div className="rounded border border-destructive/40 bg-destructive/10 px-3 py-2 text-xs text-destructive">
                        {ln.l4_notes.join(" | ")}
                      </div>
                    )}

                    {/* Token Contextual Realizations */}
                    {ln.tokens.length > 0 && (
                      <div className="flex flex-wrap gap-1.5 pl-6">
                        {ln.tokens.map((tok, tidx) => {
                          const wp = profiles[tidx];
                          const hasSandhi =
                            tok.sandhi_event &&
                            tok.sandhi_event !== "none" &&
                            tok.sandhi_event !== "preserved_final_e";
                          return (
                            <div
                              key={tidx}
                              className={`rounded border px-2 py-1.5 text-xs ${
                                hasSandhi
                                  ? "border-primary/50 bg-primary/8"
                                  : "border-border bg-background/70"
                              }`}
                            >
                              <div className="font-serif font-semibold">
                                {tok.surface}
                              </div>
                              <div className="font-mono text-xs text-foreground">
                                /{tok.ipa_realized}/
                              </div>
                              <div className="mt-0.5 font-mono text-xs text-muted-foreground num-tabular">
                                {wp ? `${wp.etymon} (${wp.earliest_year})` : ""}
                              </div>
                              {tok.sandhi_event !== "none" && (
                                <div className="mt-0.5 font-mono text-xs font-medium text-primary">
                                  {tok.sandhi_event}
                                </div>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </div>
      )}

      {/* Empirical Stratum S2 Corpus Benchmark */}
      <Card className="border-card-border bg-card shadow-xs">
        <CardHeader className="pb-3 pt-4">
          <CardTitle className="flex flex-wrap items-center justify-between gap-2 text-base font-semibold">
            <span>Empirical Stratum S2 Calibration Audit</span>
            <div className="flex gap-1.5">
              <Button
                variant={auditWork === "troilus" ? "default" : "outline"}
                size="sm"
                className="h-7 text-xs"
                onClick={() => setAuditWork("troilus")}
              >
                Troilus Book I Proem (28 lines)
              </Button>
              <Button
                variant={auditWork === "lgw" ? "default" : "outline"}
                size="sm"
                className="h-7 text-xs"
                onClick={() => setAuditWork("lgw")}
              >
                Legend of Good Women (16 lines)
              </Button>
            </div>
          </CardTitle>
        </CardHeader>
        <CardContent className="pb-4">
          {corpusAuditQuery.data ? (
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 num-tabular">
              <div className="rounded border border-border bg-background/60 p-3">
                <div className="text-xs text-muted-foreground">
                  Line Scansion Pass Rate
                </div>
                <div className="mt-1 font-mono text-lg font-semibold text-foreground">
                  {corpusAuditQuery.data.valid_lines}/
                  {corpusAuditQuery.data.total_lines} (
                  {Math.round(corpusAuditQuery.data.scansion_pass_rate * 100)}%)
                </div>
              </div>
              <div className="rounded border border-border bg-background/60 p-3">
                <div className="text-xs text-muted-foreground">
                  Phonological Rhyme Bands
                </div>
                <div className="mt-1 font-mono text-lg font-semibold text-foreground">
                  {corpusAuditQuery.data.rhyme_groups_valid}/
                  {corpusAuditQuery.data.rhyme_groups_total} Valid
                </div>
              </div>
              <div className="rounded border border-border bg-background/60 p-3">
                <div className="text-xs text-muted-foreground">
                  Sandhi / Elision Events
                </div>
                <div className="mt-1 font-mono text-lg font-semibold text-foreground">
                  {corpusAuditQuery.data.elision_count} Resolved
                </div>
              </div>
              <div className="rounded border border-border bg-background/60 p-3">
                <div className="text-xs text-muted-foreground">
                  L1 Chronology Violations
                </div>
                <div className="mt-1 font-mono text-lg font-semibold text-emerald-700 dark:text-emerald-400">
                  {corpusAuditQuery.data.l1_chronology_violations.length} (&le; 1400 CE)
                </div>
              </div>
            </div>
          ) : (
            <div className="text-xs text-muted-foreground">
              Loading S2 corpus audit...
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
