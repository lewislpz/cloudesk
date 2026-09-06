import { StatusPanel } from "@/components/ui/status-panel";

export default function WorkspaceLoading() {
  return (
    <StatusPanel
      description="Estamos preparando el contexto de tu organización."
      title="Cargando espacio de trabajo"
      tone="loading"
    />
  );
}
