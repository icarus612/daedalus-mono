// Root ESLint flat config — the shared base. Per-package configs (Phase 3.4, lane 3) re-export
// and extend this rather than duplicating rules. console.info is never flagged — standing repo
// convention — so no-console is deliberately left out of the rule set.
const js = require("@eslint/js");

module.exports = [
  js.configs.recommended,
  {
    languageOptions: {
      ecmaVersion: 2023,
      sourceType: "module",
    },
    rules: {
      "no-unused-vars": "warn",
    },
  },
  {
    ignores: ["**/node_modules/**", "**/dist/**", "**/.next/**", "**/build/**"],
  },
];
