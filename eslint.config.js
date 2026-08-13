// Root ESLint flat config — the shared base. Per-package configs (Phase 3.4, lane 3) re-export
// and extend this rather than duplicating rules. console.info is never flagged — standing repo
// convention — so no-console is deliberately left out of the rule set. Node + browser globals
// are merged because this is a mixed-runtime monorepo and the shared base cannot correctly guess
// which one any given package needs; per-package configs may narrow this later if desired.
const js = require("@eslint/js");
const globals = require("globals");

module.exports = [
  js.configs.recommended,
  {
    languageOptions: {
      ecmaVersion: 2023,
      sourceType: "module",
      globals: {
        ...globals.node,
        ...globals.browser,
      },
    },
    rules: {
      "no-unused-vars": "warn",
    },
  },
  {
    ignores: ["**/node_modules/**", "**/dist/**", "**/.next/**", "**/build/**"],
  },
];
