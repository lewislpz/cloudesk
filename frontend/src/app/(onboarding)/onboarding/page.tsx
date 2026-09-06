import Link from "next/link";

const steps = [
  ["01", "Espacio", "Pon nombre al lugar donde trabajará tu equipo."],
  ["02", "Equipo", "Invita a las personas con el acceso adecuado."],
  ["03", "Primer proyecto", "Conecta cliente, entrega y tiempo facturable."],
] as const;

export default function OnboardingPage() {
  return (
    <div className="grid gap-10 lg:grid-cols-[0.72fr_1.28fr] lg:gap-16">
      <section aria-labelledby="onboarding-heading">
        <p className="text-sm font-bold uppercase tracking-[0.18em] text-brand">
          Tres pasos
        </p>
        <h1
          className="mt-4 text-4xl font-semibold leading-tight tracking-[-0.035em] sm:text-5xl"
          id="onboarding-heading"
        >
          Prepara tu espacio sin perder el ritmo.
        </h1>
        <p className="mt-5 max-w-xl text-lg leading-8 text-muted">
          Este shell establece el recorrido. La persistencia y la identidad
          llegarán con el primer vertical de producto.
        </p>
      </section>

      <section
        aria-labelledby="progress-heading"
        className="rounded-[2rem] border border-line bg-surface p-6 shadow-panel sm:p-9"
      >
        <div className="flex items-center justify-between gap-4">
          <h2 className="text-xl font-semibold" id="progress-heading">
            Progreso de configuración
          </h2>
          <span className="text-sm font-semibold text-muted">Paso 1 de 3</span>
        </div>
        <ol aria-label="Progreso de configuración" className="mt-8 space-y-3">
          {steps.map(([number, title, description], index) => (
            <li
              aria-current={index === 0 ? "step" : undefined}
              className={`rounded-2xl border p-5 ${
                index === 0 ? "border-emerald-300 bg-emerald-50" : "border-line"
              }`}
              key={number}
            >
              <div className="flex gap-4">
                <span className="text-sm font-bold text-brand">{number}</span>
                <div>
                  <h3 className="font-semibold">{title}</h3>
                  <p className="mt-1 leading-6 text-muted">{description}</p>
                </div>
              </div>
            </li>
          ))}
        </ol>
        <div className="mt-8 flex flex-col gap-3 sm:flex-row">
          <Link
            className="inline-flex min-h-12 items-center justify-center rounded-full bg-brand px-6 font-semibold text-white hover:bg-brand-strong"
            href="/demo"
          >
            Ver espacio de ejemplo
          </Link>
          <Link
            className="inline-flex min-h-12 items-center justify-center rounded-full px-5 font-semibold text-muted hover:text-ink"
            href="/"
          >
            Volver al inicio
          </Link>
        </div>
      </section>
    </div>
  );
}
