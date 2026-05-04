import type { Artifact } from "../lib/types";

type Props = {
  artifacts: Artifact[];
};

export function ArtifactPanel({ artifacts }: Props) {
  return (
    <section className="card">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Artifacts</p>
          <h3>产物与证据</h3>
        </div>
      </div>
      {artifacts.length === 0 ? (
        <p className="muted">当前还没有产物记录。</p>
      ) : (
        <div className="artifact-list">
          {artifacts.map((artifact) => (
            <article key={artifact.id} className="artifact-item">
              <strong>{artifact.name}</strong>
              <p>
                {artifact.artifact_type} · {artifact.mime_type}
              </p>
              <code>{artifact.storage_path}</code>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
