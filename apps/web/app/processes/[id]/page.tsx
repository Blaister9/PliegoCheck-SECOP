import { ProcessDetailClient } from "./ProcessDetailClient";

export default async function ProcessDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <ProcessDetailClient processId={id} />;
}
