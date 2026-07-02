// Genera el tipo TypeScript de la interfaz NormalizedRequirement desde el
// JSON Schema versionado. La definicion canonica es el modelo Pydantic; este
// paso mantiene una unica fuente de verdad sin duplicacion manual.
import { writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { compileFromFile } from "json-schema-to-typescript";

const here = dirname(fileURLToPath(import.meta.url));
const schemaPath = join(here, "..", "generated", "normalized-requirement.schema.json");
const outputPath = join(here, "..", "generated", "normalized-requirement.ts");

const banner =
  "// Archivo generado automaticamente desde normalized-requirement.schema.json\n" +
  "// (pnpm schemas:generate). No editar a mano: la definicion canonica es el\n" +
  "// modelo Pydantic packages/schemas/src/pliegocheck_schemas/normalized_requirement.py.";

try {
  const ts = await compileFromFile(schemaPath, {
    bannerComment: banner,
    additionalProperties: false,
  });
  writeFileSync(outputPath, ts, { encoding: "utf-8" });
  console.log(`Tipo TypeScript generado en ${outputPath}`);
} catch (error) {
  console.error(`ERROR generando tipo TypeScript: ${error}`);
  process.exit(1);
}
