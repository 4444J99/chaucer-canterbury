import { useState } from "react";
import { ExternalLink, Play, Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { PilgrimDefinition, SourceGraph } from "@/lib/types";

interface CorpusSubstratePageProps {
  pilgrims: PilgrimDefinition[];
  sourceGraphs: SourceGraph[];
  onDispatchPilgrim: (pilgrimId: string) => void;
}

export function CorpusSubstratePage({
  pilgrims,
  sourceGraphs,
  onDispatchPilgrim,
}: CorpusSubstratePageProps) {
  const [subTab, setSubTab] = useState<"pilgrims" | "sources">("pilgrims");
  const [search, setSearch] = useState("");
  const [estateFilter, setEstateFilter] = useState<string>("all");

  const filteredPilgrims = pilgrims.filter((p) => {
    const matchesSearch =
      p.name.toLowerCase().includes(search.toLowerCase()) ||
      p.role_title.toLowerCase().includes(search.toLowerCase()) ||
      p.occupational_lexicon.some((w) =>
        w.toLowerCase().includes(search.toLowerCase())
      );
    if (!matchesSearch) return false;
    if (estateFilter === "silent") {
      return p.manuscript_status.includes("silent");
    }
    if (estateFilter === "bellatores") return p.estate_vector.bellatores >= 0.4;
    if (estateFilter === "oratores") return p.estate_vector.oratores >= 0.4;
    if (estateFilter === "laboratores")
      return p.estate_vector.laboratores >= 0.4;
    if (estateFilter === "urban_guild")
      return p.estate_vector.urban_guild >= 0.4;
    return true;
  });

  return (
    <div className="mx-auto max-w-7xl space-y-5">
      <div className="flex flex-col justify-between gap-3 border-b border-border pb-4 sm:flex-row sm:items-end">
        <div>
          <div className="font-mono text-xs font-semibold uppercase tracking-wider text-primary">
            CORPUS_SUBSTRATE + PILGRIM_DEFINITION
          </div>
          <h1 className="mt-0.5 text-xl font-semibold tracking-tight">
            30 General Prologue Sociolect Profiles &amp; 16 Pre-1400 S5 Source Graphs
          </h1>
          <p className="mt-1 max-w-3xl text-xs text-muted-foreground">
            Every pilgrim is parameterized from social estate, dialect ceiling, occupational lexicon, and pragmatic posture — with zero hardcoded Canterbury Tales plot assignments, enabling emergent tales for all seven historically silent pilgrims.
          </p>
        </div>

        <div className="flex gap-1.5">
          <Button
            variant={subTab === "pilgrims" ? "default" : "outline"}
            size="sm"
            onClick={() => setSubTab("pilgrims")}
            data-testid="subtab-pilgrims"
            className="h-8 text-xs num-tabular"
          >
            30 Pilgrim Agents
          </Button>
          <Button
            variant={subTab === "sources" ? "default" : "outline"}
            size="sm"
            onClick={() => setSubTab("sources")}
            data-testid="subtab-sources"
            className="h-8 text-xs num-tabular"
          >
            16 Pre-1400 S5 Sources
          </Button>
        </div>
      </div>

      {subTab === "pilgrims" ? (
        <div className="space-y-4">
          {/* Search & Estate Filter Bar */}
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="relative w-full sm:w-72">
              <Search className="pointer-events-none absolute left-2.5 top-2.5 h-3.5 w-3.5 text-muted-foreground" />
              <input
                type="search"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search pilgrim, craft, or MED lemma..."
                className="h-8 w-full rounded-md border border-input bg-background pl-8 pr-3 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-ring"
              />
            </div>

            <div className="flex flex-wrap gap-1.5">
              {[
                ["all", "All (30)"],
                ["silent", "Silent / Uncompleted in MS (7)"],
                ["bellatores", "Bellatores"],
                ["oratores", "Oratores"],
                ["laboratores", "Laboratores"],
                ["urban_guild", "Urban & Guild"],
              ].map(([key, label]) => (
                <button
                  key={key}
                  type="button"
                  onClick={() => setEstateFilter(key)}
                  data-testid={`filter-${key}`}
                  className={`rounded border px-2.5 py-1 text-xs font-medium transition-colors num-tabular ${
                    estateFilter === key
                      ? "border-primary bg-primary text-primary-foreground"
                      : "border-border bg-card text-foreground hover:bg-secondary"
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-1 gap-3.5 md:grid-cols-2 xl:grid-cols-3">
            {filteredPilgrims.map((p) => {
              const isSilent = p.manuscript_status.includes("silent");
              return (
                <Card
                  key={p.id}
                  className={`border-card-border bg-card shadow-xs ${
                    isSilent ? "ring-1 ring-primary/35" : ""
                  }`}
                >
                  <CardHeader className="pb-2 pt-3.5">
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <CardTitle className="text-sm font-semibold">
                          {p.name}
                        </CardTitle>
                        <div className="text-xs text-muted-foreground">
                          {p.role_title}
                        </div>
                      </div>
                      {isSilent ? (
                        <Badge className="bg-primary text-primary-foreground font-mono text-xs">
                          SILENT IN MS
                        </Badge>
                      ) : (
                        <Badge variant="outline" className="font-mono text-xs">
                          {p.manuscript_status}
                        </Badge>
                      )}
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-2.5 pb-3.5 text-xs">
                    <div className="grid grid-cols-2 gap-1.5 rounded border border-border/70 bg-background/60 p-2 font-mono text-xs num-tabular">
                      <div>
                        <span className="text-muted-foreground">Dialect: </span>
                        <span>{p.dialect_profile.base_region.split("_")[0]}</span>
                      </div>
                      <div>
                        <span className="text-muted-foreground">OF Ceil: </span>
                        <span>
                          {Math.round(
                            p.dialect_profile.french_prestige_ceiling * 100
                          )}
                          %
                        </span>
                      </div>
                      <div>
                        <span className="text-muted-foreground">North: </span>
                        <span>
                          {Math.round(p.dialect_profile.northernism_rate * 100)}%
                        </span>
                      </div>
                      <div>
                        <span className="text-muted-foreground">Meter Reg: </span>
                        <span>
                          {Math.round(
                            (p.prosodic_competence.metrical_regularity_target ?? 0.9) *
                              100
                          )}
                          %
                        </span>
                      </div>
                    </div>

                    <div>
                      <span className="text-muted-foreground">Oath: </span>
                      <span className="font-serif font-medium">
                        &ldquo;{p.signature_oath}&rdquo;
                      </span>
                    </div>

                    <div className="flex flex-wrap gap-1">
                      {p.occupational_lexicon.map((w) => (
                        <span
                          key={w}
                          className="rounded border border-border bg-background px-1.5 py-0.5 font-mono text-xs"
                        >
                          {w}
                        </span>
                      ))}
                    </div>

                    {p.id !== "harry_bailly" && (
                      <div className="pt-1">
                        <Button
                          variant="secondary"
                          size="sm"
                          onClick={() => onDispatchPilgrim(p.id)}
                          data-testid={`dispatch-${p.id}`}
                          className="h-7 w-full gap-1.5 text-xs font-medium"
                        >
                          <Play className="h-3 w-3" />
                          <span>Synthesize Turn as {p.name}</span>
                        </Button>
                      </div>
                    )}
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="grid grid-cols-1 gap-3.5 lg:grid-cols-2">
            {sourceGraphs.map((sg) => (
              <Card
                key={sg.source_id}
                className="border-card-border bg-card shadow-xs"
              >
                <CardHeader className="pb-2 pt-3.5">
                  <div className="flex flex-wrap items-start justify-between gap-2">
                    <div>
                      <div className="font-mono text-xs text-primary">
                        {sg.source_id} &middot; {sg.language} &middot;{" "}
                        {sg.year_composed} CE
                      </div>
                      <CardTitle className="mt-0.5 text-sm font-semibold">
                        {sg.title}
                      </CardTitle>
                      <div className="text-xs text-muted-foreground">
                        Auctor: {sg.auctor} &middot; Genre:{" "}
                        {sg.genre.replace(/_/g, " ")}
                      </div>
                    </div>
                    <Badge variant="secondary" className="font-mono text-xs num-tabular">
                      Sent {Math.round(sg.sentence_weight * 100)}% / Sol{" "}
                      {Math.round(sg.solaas_weight * 100)}%
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent className="space-y-2 pb-3.5 text-xs">
                  <div className="space-y-1.5">
                    {sg.beats.map((b, i) => (
                      <div
                        key={b.beat_id}
                        className="rounded border border-border/70 bg-background/60 px-2.5 py-1.5"
                      >
                        <span className="font-mono font-semibold text-primary num-tabular">
                          B{i + 1} [{b.edge}]
                        </span>{" "}
                        <span className="font-medium">{b.role}:</span>{" "}
                        <span className="text-muted-foreground">
                          {b.proposition}
                        </span>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Primary Corpus Provenance Links */}
          <Card className="border-card-border bg-card shadow-xs">
            <CardHeader className="pb-2 pt-3.5">
              <CardTitle className="text-sm font-semibold">
                External Philological &amp; Corpus Provenance (Strata S1–S5)
              </CardTitle>
            </CardHeader>
            <CardContent className="flex flex-wrap gap-3 pb-3.5 text-xs">
              {[
                [
                  "Middle English Dictionary (MED)",
                  "https://quod.lib.umich.edu/m/middle-english-dictionary/about",
                ],
                [
                  "CMEPV Troilus Witness",
                  "https://quod.lib.umich.edu/c/cme/Troilus/1:1.1?rgn=div2;view=fulltext",
                ],
                [
                  "Penn-Helsinki PPCME2",
                  "https://varieng.helsinki.fi/CoRD/corpora/PPCME2/",
                ],
                [
                  "Hengwrt & Ellesmere Witnesses (DHI)",
                  "https://www.dhi.ac.uk/manuscriptsonline/resources/ct/",
                ],
                [
                  "Harvard Chaucer Prosody & Final -e",
                  "https://chaucer.fas.harvard.edu/lesson-3",
                ],
              ].map(([title, url]) => (
                <a
                  key={url}
                  href={url}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-1 rounded border border-border bg-background px-2.5 py-1 font-medium text-foreground hover:border-primary hover:text-primary"
                >
                  <span>{title}</span>
                  <ExternalLink className="h-3 w-3" />
                </a>
              ))}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
