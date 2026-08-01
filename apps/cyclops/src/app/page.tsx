import Link from "next/link";

const FEATURES = [
  {
    title: "FIRST and FOLLOW, with provenance",
    body:
      "Every member of every set is tagged with the rule that put it there, so " +
      "a wrong answer points at the rule you misapplied rather than just being wrong.",
  },
  {
    title: "A parse table you fill in",
    body:
      "Type production numbers into the grid and have them checked cell by cell. " +
      "Blank is a real answer — it means the parser reports an error there.",
  },
  {
    title: "Conflicts explained, not just flagged",
    body:
      "When a grammar is not LL(1), Cyclops names the competing productions and " +
      "says whether the clash is FIRST/FIRST or FIRST/FOLLOW — and calls out left " +
      "recursion by name.",
  },
  {
    title: "Step-by-step parsing",
    body:
      "Watch the stack, the remaining input, and the production applied at each " +
      "step, all the way to accept or to the exact token that failed.",
  },
];

export default function HomePage() {
  return (
    <div className="space-y-12">
      <section className="pt-4">
        <h1 className="text-3xl font-semibold tracking-tight sm:text-4xl">
          Learn LL(1) parsing by building the table yourself
        </h1>
        <p className="mt-4 max-w-2xl text-lg text-ink-secondary">
          Cyclops computes FIRST sets, FOLLOW sets and the LL(1) parse table for
          any grammar you give it — then hands the table back empty so you can
          fill it in and find out exactly which rule you got wrong.
        </p>
        <div className="mt-6 flex flex-wrap gap-3">
          <Link href="/workbench" className="btn-primary">
            Open the workbench
          </Link>
          <Link href="/learn" className="btn-secondary">
            Read the method
          </Link>
        </div>
      </section>

      <section aria-labelledby="features-heading">
        <h2 id="features-heading" className="sr-only">
          What Cyclops does
        </h2>
        <div className="grid gap-4 sm:grid-cols-2">
          {FEATURES.map((feature) => (
            <article key={feature.title} className="card p-5">
              <h3 className="font-semibold">{feature.title}</h3>
              <p className="mt-2 text-sm text-ink-secondary">{feature.body}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="card p-6" aria-labelledby="example-heading">
        <h2 id="example-heading" className="text-lg font-semibold">
          A grammar and its table
        </h2>
        <p className="mt-2 text-sm text-ink-secondary">
          The grammar Cyclops ships with, and the table it produces. Cell{" "}
          <code>[A, b]</code> is the interesting one: <code>A</code> derives ε,
          and <code>b</code> is in <code>FOLLOW(A)</code>, so production 3 goes
          there by the second table rule.
        </p>

        <div className="mt-4 grid gap-6 lg:grid-cols-2">
          <div>
            <h3 className="mb-2 text-sm font-medium text-ink-secondary">Productions</h3>
            <ol className="space-y-1 font-mono text-sm">
              {[
                "S → A b B",
                "A → a A b",
                "A → ε",
                "B → b B",
                "B → ε",
              ].map((production, index) => (
                <li key={production} className="flex gap-3">
                  <span className="w-4 text-right text-ink-muted">{index + 1}</span>
                  <span>{production}</span>
                </li>
              ))}
            </ol>
          </div>

          <div>
            <h3 className="mb-2 text-sm font-medium text-ink-secondary">Parse table</h3>
            <div className="table-scroll">
              <table className="w-full border-collapse text-sm">
                <thead>
                  <tr className="text-ink-secondary">
                    <th scope="col" className="border-b border-line px-3 py-1.5 text-left">
                      <span className="sr-only">Non-terminal</span>
                    </th>
                    {["a", "b", "$"].map((terminal) => (
                      <th
                        key={terminal}
                        scope="col"
                        className="border-b border-line px-3 py-1.5 text-center font-mono text-xs"
                      >
                        {terminal}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {[
                    ["S", "1", "1", "—"],
                    ["A", "2", "3", "—"],
                    ["B", "—", "4", "5"],
                  ].map(([nonTerminal, ...cells]) => (
                    <tr key={nonTerminal}>
                      <th
                        scope="row"
                        className="border-b border-line px-3 py-1.5 text-left font-mono font-medium"
                      >
                        {nonTerminal}
                      </th>
                      {cells.map((cell, index) => (
                        <td
                          key={index}
                          className={`border-b border-line px-3 py-1.5 text-center font-mono ${
                            cell === "—" ? "text-ink-muted" : ""
                          }`}
                        >
                          {cell}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
