// Genera los tipos TypeScript de las interfaces desde los JSON Schema
// versionados. La definicion canonica son los modelos Pydantic; este paso
// mantiene una unica fuente de verdad sin duplicacion manual.
import { writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { compileFromFile } from "json-schema-to-typescript";

const here = dirname(fileURLToPath(import.meta.url));
const generatedDir = join(here, "..", "generated");

const CONTRACTS = [
  {
    schema: "company-profile.schema.json",
    output: "company-profile.ts",
  },
  {
    schema: "financial-evaluation.schema.json",
    output: "financial-evaluation.ts",
  },
  {
    schema: "normalized-requirement.schema.json",
    output: "normalized-requirement.ts",
  },
  {
    schema: "requirement-normalization.schema.json",
    output: "requirement-normalization.ts",
  },
  {
    schema: "manual-import.schema.json",
    output: "manual-import.ts",
  },
  {
    schema: "document-extraction.schema.json",
    output: "document-extraction.ts",
  },
];

function banner(schemaFile) {
  return (
    `// Archivo generado automaticamente desde ${schemaFile}\n` +
    "// (pnpm schemas:generate). No editar a mano: la definicion canonica son los\n" +
    "// modelos Pydantic de packages/schemas/src/pliegocheck_schemas/."
  );
}

try {
  for (const contract of CONTRACTS) {
    const ts = await compileFromFile(join(generatedDir, contract.schema), {
      bannerComment: banner(contract.schema),
      additionalProperties: false,
    });
    writeFileSync(join(generatedDir, contract.output), ts, { encoding: "utf-8" });
    console.log(`Tipo TypeScript generado: generated/${contract.output}`);
  }
} catch (error) {
  console.error(`ERROR generando tipos TypeScript: ${error}`);
  process.exit(1);
}
