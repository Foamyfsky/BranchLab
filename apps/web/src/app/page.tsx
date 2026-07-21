const readiness = [
  ["Workspace", "ready"],
  ["Simulation", "deferred"],
  ["GTFS", "inventory only"],
  ["AI", "mock mode"],
] as const;

export default function Home() {
  return (
    <main className="shell">
      <section className="placeholder" aria-labelledby="branchlab-title">
        <div className="masthead">
          <span className="eyebrow">Round 00 repository bootstrap</span>
          <h1 id="branchlab-title">BranchLab</h1>
          <p className="summary">
            The lab shell is online. Simulation, GTFS import, map rendering, branching, and GPT
            integration stay deliberately offline until their acceptance gates.
          </p>
        </div>

        <div className="status-grid" aria-label="Round 00 readiness">
          {readiness.map(([label, value]) => (
            <div className="status-tile" key={label}>
              <span className="status-label">{label}</span>
              <span className="status-value">{value}</span>
            </div>
          ))}
        </div>
      </section>
    </main>
  );
}
