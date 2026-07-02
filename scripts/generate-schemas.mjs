// Orquesta la generacion reproducible de contratos compartidos:
//   1. JSON Schema + enums TS desde el modelo canonico Pydantic.
//   2. Tipo TypeScript de la interfaz desde el JSON Schema.
//   3. Formato con la configuracion Prettier del repositorio.
// Con --check, verifica ademas que el repositorio no quede con diferencias
// en packages/schemas/generated (falla si el canonico y lo generado divergen).
//
// Script Node multiplataforma (Windows/Linux/macOS); no usa comandos de shell POSIX.
import { execSync } from "node:child_process";

const checkMode = process.argv.includes("--check");
const GENERATED_PATH = "packages/schemas/generated";

function run(command) {
  console.log(`\n> ${command}`);
  execSync(command, { stdio: "inherit" });
}

try {
  run("uv run python packages/schemas/scripts/generate.py");
  run("pnpm --filter @pliegocheck/schemas run generate:ts");
  run(`pnpm exec prettier --write ${GENERATED_PATH}`);
} catch {
  console.error("\nERROR: la generacion de contratos no pudo completarse.");
  process.exit(1);
}

if (checkMode) {
  try {
    execSync(`git diff --exit-code -- ${GENERATED_PATH}`, { stdio: "inherit" });
    const untracked = execSync(`git ls-files --others --exclude-standard -- ${GENERATED_PATH}`, {
      encoding: "utf-8",
    }).trim();
    if (untracked !== "") {
      throw new Error(`archivos generados sin versionar:\n${untracked}`);
    }
    console.log("\nschemas:check OK — modelo canonico y artefactos generados sincronizados.");
  } catch (error) {
    console.error(
      "\nERROR: los artefactos generados no coinciden con el modelo canonico.\n" +
        "Ejecuta 'pnpm schemas:generate' y confirma los cambios.\n" +
        String(error),
    );
    process.exit(1);
  }
}
