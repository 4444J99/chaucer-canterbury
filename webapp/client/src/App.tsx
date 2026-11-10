import { useEffect, useState } from "react";
import { Router, Route, Switch, useLocation } from "wouter";
import { useHashLocation } from "wouter/use-hash-location";
import { QueryClientProvider, useQuery } from "@tanstack/react-query";
import { queryClient } from "./lib/queryClient";
import { Toaster } from "@/components/ui/toaster";
import { AppShell } from "./components/AppShell";
import { GenerativeCorePage } from "./pages/GenerativeCorePage";
import { PhonologyWorkbenchPage } from "./pages/PhonologyWorkbenchPage";
import { AuthorDefinitionPage } from "./pages/AuthorDefinitionPage";
import { CorpusSubstratePage } from "./pages/CorpusSubstratePage";
import { ValidationSuitePage } from "./pages/ValidationSuitePage";
import { StudioOverview } from "./lib/types";

function StudioRouter() {
  const [isDark, setIsDark] = useState(false);
  const [pendingSpeakerOverride, setPendingSpeakerOverride] = useState<
    string | null
  >(null);
  const [, setLocation] = useLocation();

  useEffect(() => {
    document.documentElement.classList.toggle("dark", isDark);
  }, [isDark]);

  const overviewQuery = useQuery<StudioOverview>({
    queryKey: ["/api/overview"],
  });

  const handleDispatchPilgrim = (pilgrimId: string) => {
    setPendingSpeakerOverride(pilgrimId);
    setLocation("/");
  };

  return (
    <AppShell
      worldState={overviewQuery.data?.world_state}
      medCount={overviewQuery.data?.lexicon_stats.med_entries}
      isDark={isDark}
      onToggleTheme={() => setIsDark((d) => !d)}
    >
      {overviewQuery.isLoading ? (
        <div className="mx-auto max-w-7xl space-y-4">
          <div className="h-16 animate-pulse rounded-md border border-border bg-card" />
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-12">
            <div className="h-56 animate-pulse rounded-md border border-border bg-card lg:col-span-7" />
            <div className="h-56 animate-pulse rounded-md border border-border bg-card lg:col-span-5" />
          </div>
          <div className="h-96 animate-pulse rounded-md border border-border bg-card" />
        </div>
      ) : overviewQuery.isError || !overviewQuery.data ? (
        <div className="mx-auto max-w-2xl rounded-md border border-destructive/40 bg-destructive/10 p-5 text-xs">
          <div className="text-sm font-semibold text-destructive">
            Backend Protocol Engine Unreachable
          </div>
          <p className="mt-1 text-foreground">
            Unable to load /api/overview from the chaucer-canterbury FastAPI service on port 5000.
          </p>
        </div>
      ) : (
        <Switch>
          <Route path="/">
            <GenerativeCorePage
              overview={overviewQuery.data}
              pendingSpeakerOverride={pendingSpeakerOverride}
              onConsumeSpeakerOverride={() => setPendingSpeakerOverride(null)}
            />
          </Route>
          <Route path="/phonology">
            <PhonologyWorkbenchPage />
          </Route>
          <Route path="/author">
            <AuthorDefinitionPage
              author={overviewQuery.data.author_definition}
            />
          </Route>
          <Route path="/substrate">
            <CorpusSubstratePage
              pilgrims={overviewQuery.data.pilgrims}
              sourceGraphs={overviewQuery.data.source_graphs}
              onDispatchPilgrim={handleDispatchPilgrim}
            />
          </Route>
          <Route path="/validation">
            <ValidationSuitePage
              report={overviewQuery.data.counterfactual_report}
            />
          </Route>
          <Route>
            <GenerativeCorePage
              overview={overviewQuery.data}
              pendingSpeakerOverride={pendingSpeakerOverride}
              onConsumeSpeakerOverride={() => setPendingSpeakerOverride(null)}
            />
          </Route>
        </Switch>
      )}
    </AppShell>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router hook={useHashLocation}>
        <StudioRouter />
      </Router>
      <Toaster />
    </QueryClientProvider>
  );
}
