# Gemini Code Assist Prompting Library

A production-quality prompting framework for Gemini Code Assist that enforces strict development standards through automated hooks and structured commands.

## Structure

```
.
├── GEMINI.md                         # Core development partnership guidelines
├── commands/                         # Command templates for various workflows
│   ├── check.md                     # Validation and checking workflows
│   ├── next.md                      # Production implementation workflow
│   └── prompt.md                    # Prompt synthesis from templates
├── hooks/                            # Automated code quality enforcement
│   ├── common-helpers.sh            # Shared utilities
│   ├── example-gemini-hooks-config.sh # Example configuration
│   ├── example-gemini-hooks-ignore  # Example ignore patterns
│   ├── ntfy-notifier.sh             # Push notifications for task completion
│   ├── README.md                    # Hook documentation
│   ├── smart-lint.sh                # Multi-language linting and formatting
│   └── smart-test.sh                # Intelligent testing workflows
├── default.nix                      # Nix package definition
└── settings.json                    # Gemini Code Assist configuration
```

## Key Features

- **Zero-tolerance quality standards** - All code must pass linting with no warnings
- **Multi-language support** - Go, Python, JavaScript/TypeScript, Rust, Nix
- **Automated validation** - Hooks run after every file modification
- **Research-first workflow** - Enforces proper planning before implementation
- **Agent orchestration** - Templates for spawning multiple specialized agents

## Usage

The framework is designed to be used with Gemini Code Assist's command system. Main entry points:

- `commands/next.md` - Complete implementation workflow
- `commands/prompt.md` - Synthesize prompts with specific arguments
- `hooks/smart-lint.sh` - Multi-language code quality validation

## Configuration

Project-specific settings can be configured via:
- `gemini-code-hooks-config.sh` - Hook behavior customization
- `gemini-code-hooks-ignore` - Files to exclude from validation
- Environment variables for global defaults