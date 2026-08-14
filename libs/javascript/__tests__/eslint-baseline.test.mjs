#!/usr/bin/env node
// eslint-baseline.test.mjs
//
// Contract under test: every active JS package's `lint` script must run REAL
// ESLint using a config that ultimately derives from the shared root
// eslint.config.js. That shared base deliberately omits `no-console`, so
// `console.info(...)` must never be flagged. It DOES enable
// `eslint:recommended`, so a genuine `no-undef` violation (referencing an
// undeclared variable) must fail the lint run.
//
// This script proves the shared base config itself behaves as contracted by
// shelling out to the real `eslint` binary against the root eslint.config.js,
// using fixtures it builds itself. It does not depend on, read, or import any
// package source anywhere else in the repo.
//
// Run directly: node libs/javascript/__tests__/eslint-baseline.test.mjs

import { execFileSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// libs/javascript/__tests__ -> libs/javascript -> libs -> repo root
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const rootEslintConfig = path.join(repoRoot, "eslint.config.js");

const eslintBinCandidates = [
  path.join(repoRoot, "node_modules", ".bin", "eslint"),
  path.join(repoRoot, "node_modules", ".bin", "eslint.cmd"),
];
const eslintBin = eslintBinCandidates.find((p) => fs.existsSync(p));

const failures = [];
const passes = [];

function check(label, condition, detail) {
  if (condition) {
    passes.push(label);
    console.log(`PASS: ${label}`);
  } else {
    failures.push(label);
    console.error(`FAIL: ${label}${detail ? ` -- ${detail}` : ""}`);
  }
}

function runEslint(targetFile) {
  const args = ["--no-config-lookup", "--config", rootEslintConfig, targetFile];
  try {
    // ESLint's flat-config "base path" defaults to the current working
    // directory; a fixture living outside that base path is silently
    // ignored (a warning, not a lint result) rather than actually linted.
    // Running with cwd set to the fixture's own directory keeps the
    // fixture inside its base path so the config's rules actually apply.
    const stdout = execFileSync(eslintBin, args, {
      encoding: "utf8",
      stdio: ["ignore", "pipe", "pipe"],
      cwd: path.dirname(targetFile),
    });
    return { status: 0, stdout, stderr: "" };
  } catch (err) {
    // execFileSync throws when the child process exits non-zero.
    return {
      status: typeof err.status === "number" ? err.status : 1,
      stdout: err.stdout ? err.stdout.toString() : "",
      stderr: err.stderr ? err.stderr.toString() : "",
    };
  }
}

function main() {
  if (!fs.existsSync(rootEslintConfig)) {
    console.error(`FAIL: root eslint.config.js not found at ${rootEslintConfig}`);
    process.exit(1);
  }
  if (!eslintBin) {
    console.error(
      `FAIL: could not locate an eslint binary under ${repoRoot}/node_modules/.bin`
    );
    process.exit(1);
  }

  const workDir = fs.mkdtempSync(path.join(os.tmpdir(), "eslint-baseline-test-"));
  const cleanFixture = path.join(workDir, "console-info-fixture.js");
  const violationFixture = path.join(workDir, "no-undef-fixture.js");

  try {
    // Fixture 1: console.info inside an otherwise rule-clean module.
    // The shared base config deliberately omits no-console, so this must
    // lint cleanly (exit code 0).
    const cleanFixtureSource = [
      "function logMessage(value) {",
      '  console.info("test");',
      "  return value;",
      "}",
      "",
      "export default logMessage;",
      "",
    ].join("\n");
    fs.writeFileSync(cleanFixture, cleanFixtureSource, "utf8");

    const cleanResult = runEslint(cleanFixture);
    check(
      "console.info is not flagged (eslint exits 0 on a console.info-only fixture)",
      cleanResult.status === 0,
      `exit status=${cleanResult.status}, stdout=${JSON.stringify(cleanResult.stdout)}, stderr=${JSON.stringify(cleanResult.stderr)}`
    );

    // Fixture 2: a genuine undefined-variable reference. eslint:recommended
    // enables no-undef at error level, so this must fail the lint run and
    // the output must name the rule.
    const violationFixtureSource = [
      "export default definitelyNotDeclaredAnywhere;",
      "",
    ].join("\n");
    fs.writeFileSync(violationFixture, violationFixtureSource, "utf8");

    const violationResult = runEslint(violationFixture);
    const violationOutput = `${violationResult.stdout}${violationResult.stderr}`;
    check(
      "no-undef violation causes eslint to exit non-zero",
      violationResult.status !== 0,
      `exit status=${violationResult.status}`
    );
    check(
      "no-undef violation output mentions the no-undef rule",
      violationOutput.includes("no-undef"),
      `output=${JSON.stringify(violationOutput)}`
    );
  } finally {
    // Clean up fixtures regardless of assertion outcome.
    for (const f of [cleanFixture, violationFixture]) {
      if (fs.existsSync(f)) fs.rmSync(f);
    }
    fs.rmSync(workDir, { recursive: true, force: true });
  }

  console.log("");
  console.log(`Summary: ${passes.length} passed, ${failures.length} failed`);
  if (failures.length > 0) {
    console.error(`Failing checks: ${failures.join("; ")}`);
    process.exit(1);
  }
  process.exit(0);
}

main();
