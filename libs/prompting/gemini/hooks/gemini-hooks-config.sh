#!/usr/bin/env bash
# Example configuration for Gemini Code Assist hooks.
# Copy this to your project root as `gemini-code-hooks-config.sh` and customize.

# --- GLOBAL SETTINGS ---

# Enable or disable all hooks globally
# export GEMINI_HOOKS_ENABLED="true"

# Enable debug output for all hooks
# export GEMINI_HOOKS_DEBUG="1"

# --- SMART-LINT SETTINGS ---

# Enable/disable linting for specific languages
# export GEMINI_HOOKS_GO_ENABLED="true"
# export GEMINI_HOOKS_PYTHON_ENABLED="true"
# export GEMINI_HOOKS_JS_ENABLED="true"
# export GEMINI_HOOKS_RUST_ENABLED="true"
# export GEMINI_HOOKS_NIX_ENABLED="true"

# --- SMART-TEST SETTINGS ---

# Enable or disable running tests automatically after an edit
# export GEMINI_HOOKS_TEST_ON_EDIT="true"

# Configure which test modes to run, comma-separated.
# Options: focused, package, all, integration
# export GEMINI_HOOKS_TEST_MODES="focused,package"

# Enable or disable Go's race detector during tests
# export GEMINI_HOOKS_ENABLE_RACE="true"

# Fail the hook if a test file is missing for a source file
# export GEMINI_HOOKS_FAIL_ON_MISSING_TESTS="false"

# Show verbose output even for successful tests
# export GEMINI_HOOKS_TEST_VERBOSE="false"