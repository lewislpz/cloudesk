import type { ReactNode } from "react";

type StatusTone = "empty" | "error" | "loading";

type StatusPanelProps = Readonly<{
  action?: ReactNode;
  description: string;
  title: string;
  tone: StatusTone;
}>;

const toneStyles: Record<StatusTone, string> = {
  empty: "border-line bg-surface",
  error: "border-red-200 bg-red-50",
  loading: "border-emerald-200 bg-emerald-50",
};

const toneMarks: Record<StatusTone, string> = {
  empty: "—",
  error: "!",
  loading: "…",
};

export function StatusPanel({
  action,
  description,
  title,
  tone,
}: StatusPanelProps) {
  const isError = tone === "error";

  return (
    <section
      aria-busy={tone === "loading" || undefined}
      aria-label={title}
      aria-live={isError ? "assertive" : "polite"}
      className={`rounded-3xl border p-6 shadow-sm sm:p-8 ${toneStyles[tone]}`}
      role={isError ? "alert" : "status"}
    >
      <span
        aria-hidden="true"
        className="mb-5 grid size-10 place-items-center rounded-full bg-ink text-lg font-semibold text-white"
      >
        {toneMarks[tone]}
      </span>
      <h2 className="text-xl font-semibold tracking-tight text-ink">{title}</h2>
      <p className="mt-2 max-w-xl leading-7 text-muted">{description}</p>
      {action ? <div className="mt-6">{action}</div> : null}
    </section>
  );
}
