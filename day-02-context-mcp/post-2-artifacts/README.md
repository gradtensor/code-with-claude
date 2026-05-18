# Post 2 artifacts

Raw outputs captured on 2026-05-18 from real runs against `claude-sonnet-4-6`. These are the evidence files quoted from in Post 2. They are snapshots, not regenerated automatically. Reruns will produce different outputs.

Pricing constants used: `PRICE_IN=$3.00/Mtok`, `PRICE_OUT=$15.00/Mtok` (rough Sonnet 4.6 list pricing). Costs are estimates from those constants, not actual billed amounts.

## Files

### `stuff_everything_rd_3runs.txt`

Three runs of `day-02-context-mcp/stuff_everything.py` on the question:

> What are all the R&D-related allocations in this Budget, across all sectors?

Demonstrates variance under the "stuff the whole speech into every prompt" baseline. Input tokens are constant across runs (27,505) because the same full speech is sent each time. Output content and emphasis vary.

Aggregate: 82,515 input + 2,584 output = $0.2863 across three runs.

### `with_mcp_rd_3runs.txt`

Same question, three runs of `day-02-context-mcp/with_mcp.py`. The model decides which sections to fetch via MCP each run. Input tokens vary (36,890 / 24,216 / 23,517) because the model picks different combinations of sections.

Aggregate: 84,623 input + 7,093 output = $0.3603 across three runs.

Counter-intuitive but real: on a broad cross-cutting question like this, MCP is slightly *more* expensive than stuff-everything because the model fetches many sections and accumulates them in context. The MCP cost win shows up on focused questions, not on sweeping ones.

### `with_mcp_textile_trace.txt`

Single run of `with_mcp.py --show-trace` on:

> How does this Budget affect the textile industry?

Shows the model's tool-call sequence: 1 `list_budget_sections` call followed by 4 `read_budget_section` calls. Sections fetched were `manufacturing.textile_integrated_programme`, plus three indirect-tax sections relevant to textile exports. Demonstrates cross-Part reasoning by the model.

Single run: 16,469 input + 1,418 output = $0.0707.

### `with_mcp_rd_trace.txt`

Single run of `with_mcp.py --show-trace` on the R&D question, for direct comparison against `with_mcp_textile_trace.txt`. 1 list call + 11 read calls = 12 total tool calls. The model swept through nearly every Part A section plus two Part B sections.

Single run: 25,412 input + 2,620 output = $0.1155.

## Use in Post 2

These files are the source of every variance, cost, and tool-call number quoted in Post 2. Quote them directly. Trim or anonymise as needed, but do not paraphrase the numbers.
