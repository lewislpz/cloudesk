import Link from "next/link";

const outcomes = [
  [
    "01",
    "Entrega",
    "Organiza clientes, proyectos y tareas sin perder el contexto.",
  ],
  [
    "02",
    "Tiempo",
    "Conecta cada hora facturable con el trabajo que la originó.",
  ],
  [
    "03",
    "Cobro",
    "Convierte actividad confirmada en una facturación trazable.",
  ],
] as const;

export default function PublicPage() {
  return (
    <>
      <section className="mx-auto grid max-w-7xl gap-12 px-5 pb-20 pt-16 sm:px-8 sm:pt-24 lg:grid-cols-[1.15fr_0.85fr] lg:px-12 lg:pb-28 lg:pt-32">
        <div>
          <p className="mb-6 inline-flex rounded-full border border-emerald-200 bg-emerald-50 px-4 py-2 text-sm font-semibold text-brand">
            Operaciones para equipos de servicios
          </p>
          <h1 className="max-w-4xl text-5xl font-semibold leading-[0.98] tracking-[-0.05em] text-ink sm:text-6xl lg:text-7xl">
            Haz visible el camino de tu trabajo facturable.
          </h1>
          <p className="mt-7 max-w-2xl text-lg leading-8 text-muted sm:text-xl">
            ClouDesk reúne entrega, tiempo y facturación en un espacio sencillo,
            trazable y preparado para crecer con tu equipo.
          </p>
          <div className="mt-9 flex flex-col gap-3 sm:flex-row">
            <Link
              className="inline-flex min-h-12 items-center justify-center rounded-full bg-brand px-6 font-semibold text-white hover:bg-brand-strong"
              href="/onboarding"
            >
              Configurar espacio
            </Link>
            <Link
              className="inline-flex min-h-12 items-center justify-center rounded-full border border-line bg-surface px-6 font-semibold text-ink hover:border-muted"
              href="/demo"
            >
              Explorar el shell
            </Link>
          </div>
        </div>

        <aside
          aria-label="Resumen del flujo"
          className="self-end rounded-[2rem] border border-line bg-surface p-5 shadow-panel sm:p-7"
        >
          <div className="flex items-center justify-between border-b border-line pb-5">
            <div>
              <p className="text-sm font-semibold text-muted">Esta semana</p>
              <p className="mt-1 text-3xl font-semibold tracking-tight">
                32,5 h
              </p>
            </div>
            <span className="rounded-full bg-amber-100 px-3 py-1 text-sm font-semibold text-amber-900">
              Vista de ejemplo
            </span>
          </div>
          <div className="space-y-3 pt-5">
            {outcomes.map(([number, title]) => (
              <div
                className="flex items-center gap-4 rounded-2xl bg-canvas p-4"
                key={number}
              >
                <span className="text-xs font-bold text-brand">{number}</span>
                <span className="font-semibold">{title}</span>
                <span aria-hidden="true" className="ml-auto text-muted">
                  →
                </span>
              </div>
            ))}
          </div>
        </aside>
      </section>

      <section
        aria-labelledby="workflow-heading"
        className="border-y border-line bg-surface"
      >
        <div className="mx-auto max-w-7xl px-5 py-16 sm:px-8 lg:px-12 lg:py-20">
          <p className="text-sm font-bold uppercase tracking-[0.18em] text-brand">
            Un único hilo
          </p>
          <h2
            className="mt-3 max-w-2xl text-3xl font-semibold tracking-tight sm:text-4xl"
            id="workflow-heading"
          >
            Menos saltos entre herramientas. Más contexto compartido.
          </h2>
          <div className="mt-10 grid gap-4 md:grid-cols-3">
            {outcomes.map(([number, title, description]) => (
              <article
                className="rounded-3xl border border-line p-6"
                key={number}
              >
                <p className="text-sm font-bold text-brand">{number}</p>
                <h3 className="mt-8 text-xl font-semibold">{title}</h3>
                <p className="mt-3 leading-7 text-muted">{description}</p>
              </article>
            ))}
          </div>
        </div>
      </section>
    </>
  );
}
