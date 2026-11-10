import { ReactNode, useState } from "react";
import { Link, useLocation } from "wouter";
import {
  BookOpen,
  Compass,
  Feather,
  FlaskConical,
  Menu,
  Moon,
  Sliders,
  Sun,
  X,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { WorldState } from "@/lib/types";

interface NavItem {
  href: string;
  code: string;
  label: string;
  icon: typeof Compass;
}

const NAV_ITEMS: NavItem[] = [
  {
    href: "/",
    code: "GENERATIVE_CORE",
    label: "Pilgrimage & Synthesis",
    icon: Compass,
  },
  {
    href: "/phonology",
    code: "PHONOLOGY_WORKBENCH",
    label: "IPA & Final -e Scansion",
    icon: Feather,
  },
  {
    href: "/author",
    code: "AUTHOR_DEFINITION",
    label: "Operator Calibration",
    icon: Sliders,
  },
  {
    href: "/substrate",
    code: "CORPUS_SUBSTRATE",
    label: "Pilgrims & S5 Sources",
    icon: BookOpen,
  },
  {
    href: "/validation",
    code: "VALIDATION_SUITE",
    label: "Holdout Counterfactuals",
    icon: FlaskConical,
  },
];

interface AppShellProps {
  children: ReactNode;
  worldState?: WorldState;
  medCount?: number;
  isDark: boolean;
  onToggleTheme: () => void;
}

export function AppShell({
  children,
  worldState,
  medCount,
  isDark,
  onToggleTheme,
}: AppShellProps) {
  const [location] = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);

  const renderNavLinks = (onSelect?: () => void) => (
    <nav className="flex flex-col gap-1 px-3 py-3" aria-label="Primary modules">
      {NAV_ITEMS.map((item) => {
        const active =
          item.href === "/"
            ? location === "/" || location === ""
            : location.startsWith(item.href);
        const Icon = item.icon;
        return (
          <Link
            key={item.href}
            href={item.href}
            onClick={onSelect}
            data-testid={`nav-${item.code.toLowerCase()}`}
            className={`group flex items-start gap-2.5 rounded-md px-2.5 py-2 text-left transition-colors ${
              active
                ? "bg-primary text-primary-foreground shadow-xs"
                : "text-sidebar-foreground hover:bg-sidebar-accent"
            }`}
          >
            <Icon
              className={`mt-0.5 h-4 w-4 shrink-0 ${
                active ? "text-primary-foreground" : "text-muted-foreground group-hover:text-foreground"
              }`}
            />
            <div className="min-w-0 flex-1">
              <div
                className={`font-mono text-xs font-medium tracking-tight ${
                  active ? "text-primary-foreground" : "text-foreground"
                }`}
              >
                {item.code}
              </div>
              <div
                className={`truncate text-xs ${
                  active ? "text-primary-foreground/85" : "text-muted-foreground"
                }`}
              >
                {item.label}
              </div>
            </div>
          </Link>
        );
      })}
    </nav>
  );

  return (
    <div className="flex min-h-screen w-full bg-background text-foreground">
      {/* Desktop Persistent Sidebar */}
      <aside className="hidden w-64 shrink-0 flex-col border-r border-sidebar-border bg-sidebar lg:flex">
        <div className="border-b border-sidebar-border px-4 py-4">
          <div className="font-mono text-xs font-semibold uppercase tracking-wider text-primary">
            Protocol Engine v1.0
          </div>
          <div className="mt-0.5 text-base font-semibold tracking-tight text-sidebar-foreground">
            chaucer-canterbury
          </div>
          <p className="mt-1 text-xs leading-relaxed text-muted-foreground">
            Pre-GVS London Middle English phonology, sociolect conditioning, and holdout-blind synthesis.
          </p>
        </div>

        <div className="flex-1 overflow-y-auto">{renderNavLinks()}</div>

        {/* Substrate Invariant Footer */}
        <div className="border-t border-sidebar-border px-4 py-3 text-xs text-muted-foreground">
          <div className="flex items-center justify-between py-0.5">
            <span>Epistemic Horizon</span>
            <span className="font-mono font-medium text-foreground num-tabular">
              &le; 1400 CE
            </span>
          </div>
          <div className="flex items-center justify-between py-0.5">
            <span>MED Lexicon (S4)</span>
            <span className="font-mono font-medium text-foreground num-tabular">
              {medCount ?? 267} lemmas
            </span>
          </div>
          <div className="flex items-center justify-between py-0.5">
            <span>Holdout Stratum (S1)</span>
            <span className="font-mono text-primary font-medium">ISOLATED</span>
          </div>
        </div>
      </aside>

      {/* Mobile Drawer Overlay */}
      {mobileOpen && (
        <div className="fixed inset-0 z-50 flex lg:hidden">
          <div
            className="fixed inset-0 bg-black/50"
            onClick={() => setMobileOpen(false)}
          />
          <div className="relative z-10 flex w-72 max-w-[85vw] flex-col border-r border-sidebar-border bg-sidebar">
            <div className="flex items-center justify-between border-b border-sidebar-border px-4 py-3">
              <div>
                <div className="font-mono text-xs font-semibold text-primary">
                  Protocol Engine v1.0
                </div>
                <div className="text-sm font-semibold">chaucer-canterbury</div>
              </div>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setMobileOpen(false)}
                aria-label="Close navigation"
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
            <div className="flex-1 overflow-y-auto">
              {renderNavLinks(() => setMobileOpen(false))}
            </div>
          </div>
        </div>
      )}

      {/* Main Content Column */}
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-30 flex flex-wrap items-center justify-between gap-3 border-b border-border bg-background/95 px-4 py-2.5 backdrop-blur-xs lg:px-6">
          <div className="flex items-center gap-2.5">
            <Button
              variant="outline"
              size="icon"
              className="h-8 w-8 lg:hidden"
              onClick={() => setMobileOpen(true)}
              aria-label="Open navigation"
              data-testid="mobile-menu-btn"
            >
              <Menu className="h-4 w-4" />
            </Button>
            {worldState ? (
              <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs">
                <span className="inline-flex items-center gap-1.5 rounded-md border border-border bg-card px-2.5 py-1 font-medium">
                  <span className="h-2 w-2 rounded-full bg-primary" />
                  <span>{worldState.route_stage_name}</span>
                  <span className="font-mono text-muted-foreground num-tabular">
                    (Mile {worldState.mile_marker}/56)
                  </span>
                </span>
                <span className="hidden sm:inline-flex items-center gap-2 rounded-md border border-border bg-card px-2.5 py-1 num-tabular">
                  <span className="text-muted-foreground">Turn</span>
                  <span className="font-mono font-semibold">{worldState.turn_index}</span>
                  <span className="text-border">|</span>
                  <span className="text-muted-foreground">Sentence</span>
                  <span className="font-mono font-semibold">
                    {Math.round(worldState.rolling_sentence_level * 100)}%
                  </span>
                  <span className="text-muted-foreground">Solaas</span>
                  <span className="font-mono font-semibold">
                    {Math.round(worldState.rolling_solaas_level * 100)}%
                  </span>
                </span>
              </div>
            ) : (
              <span className="text-xs text-muted-foreground">
                Initializing WORLD_STATE...
              </span>
            )}
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={onToggleTheme}
              data-testid="theme-toggle-btn"
              className="h-8 gap-1.5 text-xs"
            >
              {isDark ? (
                <>
                  <Sun className="h-3.5 w-3.5" />
                  <span>Vellum Light</span>
                </>
              ) : (
                <>
                  <Moon className="h-3.5 w-3.5" />
                  <span>Scriptorium Dark</span>
                </>
              )}
            </Button>
          </div>
        </header>

        <main className="flex-1 px-4 py-5 lg:px-6 lg:py-6">{children}</main>
      </div>
    </div>
  );
}
