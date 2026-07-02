// Comandos Alembic multiplataforma usados por package.json.
import { execFileSync } from "node:child_process";

const command = process.argv[2];

function run(args) {
  console.log(`\n> uv ${args.join(" ")}`);
  execFileSync("uv", args, { stdio: "inherit" });
}

if (command === "migrate") {
  run(["run", "alembic", "-c", "apps/api/alembic.ini", "upgrade", "head"]);
} else if (command === "check") {
  run(["run", "alembic", "-c", "apps/api/alembic.ini", "current"]);
  run(["run", "alembic", "-c", "apps/api/alembic.ini", "check"]);
} else {
  console.error("Uso: node scripts/db.mjs <migrate|check>");
  process.exit(1);
}
