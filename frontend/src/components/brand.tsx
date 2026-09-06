import Link from "next/link";

export function Brand() {
  return (
    <Link
      aria-label="ClouDesk, inicio"
      className="inline-flex min-h-11 items-center gap-3 rounded-md font-semibold tracking-tight text-ink"
      href="/"
    >
      <span
        aria-hidden="true"
        className="grid size-9 place-items-center rounded-xl bg-brand text-sm font-bold text-white"
      >
        CD
      </span>
      <span className="text-lg">ClouDesk</span>
    </Link>
  );
}
