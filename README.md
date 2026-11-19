# 🕷️ Stealth Browser Agent & Website Auditor

An automated, anti-bot resilient website audit and scraping framework powered by the **Model Context Protocol (MCP)**, **Patchright** (stealth Chromium automation), and autonomous AI agent CLIs (**Claude Code** or **Google Antigravity CLI**).

---

## 📖 Overview

This project bridges autonomous AI agents with a specialized, humanized browser engine. Rather than relying on simple HTTP requests or easily detectable automation libraries, this tool spins up an anti-detect Chromium browser instance alongside a local Streamable HTTP MCP server (`human-browser-mcp`). 

The agent navigates the web through human-like interactions—utilizing Bézier curve mouse trajectories, Gaussian jitter, realistic typing cadences, and smooth scrolling—to perform in-depth compliance, high-risk activity, and foreign jurisdiction audits.

### Key Features

- **Anti-Bot & Stealth Automation:** Built on `patchright` to bypass automated bot detection (`--disable-blink-features=AutomationControlled`, persistent user-data profiles, and custom Chrome channel execution).
- **Humanized Interaction Engine:**
  - Mouse movement based on cubic Bézier curves with randomized speed and natural Gaussian jitter.
  - Natural typing cadence with configurable characters-per-minute (CPM) and backspace error correction.
  - Human dwell times, micro-pauses, and realistic mouse-wheel scrolling increments.
- **Model Context Protocol (MCP) Server:** Exposes a streamable HTTP MCP server on `http://127.0.0.1:<port>/mcp` providing fine-grained browser tools to the LLM agent.
- **Multi-Provider AI Orchestration:** Out-of-the-box integration with:
  - **Claude Code CLI** (`claude`)
  - **Antigravity CLI** (`agy`)
- **Automated Website Audit Protocol:** Employs pre-packaged agent skills to systematically inspect websites, detect high-risk business verticals, assess prohibited jurisdictions/currencies, catalog third-party connections, and record screenshot evidence.

---

## 🏗️ Architecture

```
                                  +-----------------------------+
                                  |     CLI Command (scraper)   |
                                  +--------------+--------------+
                                                 |
                   +-----------------------------+-----------------------------+
                   |                                                           |
                   v                                                           v
+--------------------------------------+                     +-----------------------------------+
|     Streamable HTTP MCP Server       |                     |     AI Agent Process (Subprocess) |
|      (Default: Port 3001)            |                     |      (Claude Code or AGY CLI)     |
+------------------+-------------------+                     +-----------------+-----------------+
                   |                                                           |
                   | Exposes Browser Tools                                     | Sends Commands
                   | (goto, click, hover, screenshot, ...)                     | (/website-audit)
                   |                                                           |
                   + < - - - - - - [ JSON-RPC / MCP ] - - - - - - - - - - - - -+
                   |
                   v
+--------------------------------------+
|       Patchright / Chromium          |
|    (Humanized Mouse & Typing,        |
|     DOM Snapshots, Screenshots)      |
+------------------+-------------------+
                   |
                   v
+--------------------------------------+
|      Target Website under Audit      |
+--------------------------------------+
```

---

## 📦 Prerequisites

1. **Python:** Version `>= 3.14`
2. **Package Manager:** [`uv`](https://docs.astral.sh/uv/) (recommended) or standard Python `pip`
3. **Google Chrome / Chromium:** Installed on your system
4. **Agent CLI:** Ensure at least one of the supported provider CLIs is installed and authenticated:
   - **Claude Code CLI (`claude`):** Authenticated via Anthropic API or custom gateway.
   - **Google Antigravity CLI (`agy`):** Configured and accessible in your system `PATH`.

---

## 🚀 Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/c1nnam0nbun/website-auditor
   cd scraper
   ```

2. **Install dependencies:**
   Using `uv`:
   ```bash
   uv sync
   ```
   Or using standard `pip`:
   ```bash
   pip install -e .
   ```

3. **Install Browser Binaries:**
   Ensure Patchright / Playwright browser binaries are installed:
   ```bash
   uv run patchright install chromium
   ```

---

## ⚙️ Configuration

The application reads a JSON configuration file specifying the AI agent provider, model selection, reasoning effort, and environment variables.

### Configuration Schema

```json
{
  "provider": "antigravity | claude",
  "model": "model-identifier-string",
  "effort": "low | medium | high",
  "env": {
    "KEY": "VALUE"
  }
}
```

### Configuration Fields

| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `provider` | `string` | **Yes** | The agent CLI provider to use. Must be either `"antigravity"` (for AGY) or `"claude"` (for Claude Code). |
| `model` | `string` | No | Specific model identifier to pass to the CLI (e.g. `gemini-3.8-flash` or `claude-sonnet-5-5`). |
| `effort` | `string` | No | Reasoning/thinking effort level. Defaults to `"medium"`. |
| `env` | `object` | No | Key-value pairs of environment variables injected into the agent CLI subprocess (e.g., API keys, proxy endpoints, or gateway URLs). |

### Example Configurations

#### 1. Google Antigravity (`config-agy.json`)
```json
{
  "provider": "antigravity",
  "model": "gemini-3.8-flash",
  "effort": "medium"
}
```

#### 2. Claude Code (`config-claude.json`)
```json
{
  "provider": "claude",
  "model": "claude-sonnet-5-5",
  "env": {
    "ANTHROPIC_AUTH_TOKEN": "",
    "ANTHROPIC_API_KEY": "your-api-key-here"
  }
}
```

### Agent MCP Server Registration

The agent discovers the browser tools through MCP configuration files:
- **Antigravity CLI:** `.agents/mcp_config.json`
- **Claude Code:** `.claude/mcp_config.json`

Both files point the agent to the MCP endpoint:
```json
{
  "mcpServers": {
    "human-browser-mcp": {
      "serverUrl": "http://127.0.0.1:3001/mcp"
    }
  }
}
```

---

## 💻 Usage & CLI Options

Run the CLI using `uv run scraper` or directly via `scraper` (if installed in the active virtual environment).

### Syntax

```bash
uv run scraper --url <url> --workdir <workdir>
```

### Options Reference

| Option | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `--url` | `TEXT` | `None` | **Target Website URL** to audit (e.g., `https://example.com`). |
| `--workdir` | `TEXT` | `None` | **Working directory** where audit output files, reports, snapshots, and screenshots will be saved. |
| `--config` | `TEXT` | `./config.json` | Path to the JSON configuration file defining provider and environment settings. |
| `--port` | `INTEGER` | `3001` | Port on which the Streamable HTTP MCP server will listen. |
| `--help` | `FLAG` | — | Show help message and exit. |

### Command Examples

#### Run an audit with Google Antigravity
```bash
uv run scraper --config config-agy.json --url https://example.com --workdir ./output/example_audit
```

#### Run an audit with Claude Code on a custom port
```bash
uv run scraper --config config-claude.json --port 3005 --url https://target-site.com --workdir ./output/target_audit
```

---

## 🛠️ MCP Tools Reference

The `human-browser-mcp` server provides the following browser automation tools to the LLM agent:

| Tool Name | Parameters | Description |
| :--- | :--- | :--- |
| `goto` | `url: str` | Navigates the browser to the specified URL. Removes non-essential elements (`<script>`, `<style>`, `<svg>`) and saves a cleaned HTML snapshot to `snapshots/`. Returns the snapshot file path. |
| `contents` | *None* | Returns the complete, unstripped HTML source code of the active page. |
| `hover` | `selector: str` | Smoothly moves the mouse via Bézier curves to hover over the element specified by the CSS selector. Returns a simplified DOM snapshot. |
| `click` | `selector: str`, `button: "left" \| "right" \| "middle"` | Moves to the element and performs a humanized click. Automatically waits 5 seconds and awaits network idle. Returns a DOM snapshot. |
| `screenshot` | `full_page: bool = False`, `selector: str = ""` | Captures a screenshot of the entire page or a specific CSS selector element. Scales dimensions with Lanczos resampling into `screenshots/<timestamp>.jpeg`. |
| `type_text` | `text: str`, `selector: str = ""` | Focuses/clicks the element and types text using simulated human typing speeds (CPM) and inter-key latency. |
| `scroll_to_selector` | `selector: str` | Smoothly scrolls the window until the element matched by the CSS selector is in the viewport. |
| `scroll_by_pixels` | `delta_y: int` | Emulates mouse wheel scrolling in stepped intervals by the given vertical pixel delta. |
| `back` | *None* | Navigates back in browser history, awaiting network idle. |

---

## 📄 Audit Output Artifacts

When an audit is executed, all outputs are written directly to the directory specified in `--workdir`:

1. **`report.md`**: The structured compliance and risk assessment report containing:
   - Target URL and audit status (`Completed` or `Aborted due to Anti-Bot`).
   - Flagged risk categories (high-risk activities, restricted jurisdictions, sanctioned currencies).
   - Detailed reproduction steps and embedded screenshot evidence.
   - Anti-bot / challenge encounter logs.
   - Final audit conclusion and risk summary.
2. **`connections.md`**: A markdown table documenting all third-party and external domains detected during navigation.
3. **`feature_request.md`**: Logs any interaction requirements encountered that exceeded standard browser tool capabilities.
4. **`snapshots/`**: Cleaned, text-focused HTML DOM snapshots utilized by the agent during navigation.
5. **`screenshots/`**: Visual captures taken during page evaluation to preserve audit evidence.
6. **`file.log`**: Application execution logs generated by `loguru`.

---

## 📂 Project Structure

```
├── .agents/
│   ├── mcp_config.json               # MCP server configuration for Antigravity CLI
│   └── skills/website-audit/SKILL.md # Audit instructions and guidelines for AGY
├── .claude/
│   ├── mcp_config.json               # MCP server configuration for Claude Code
│   ├── settings.local.json           # Claude Code MCP server permissions
│   └── skills/website-audit/SKILL.md # Audit instructions and guidelines for Claude
├── config-agy.json                   # Example configuration for Antigravity CLI
├── config-claude.json                # Example configuration for Claude Code
├── data/                             # Persistent browser user data and profile storage
├── pyproject.toml                    # UV / Python package definition and dependencies
├── src/
│   └── scraper/
│       ├── __init__.py               # CLI entrypoint, MCP server & provider orchestration
│       └── human.py                  # Patchright wrapper, Bézier curves & stealth humanization
└── README.md                         # Project documentation
```

---

## 🛡️ Anti-Bot Handling & Best Practices

- **Browser Profile:** Browser sessions utilize a persistent context located at `./data` (`user_data_dir`) to retain cookies, local storage, and avoid fresh-fingerprint alarms.
- **Bot Defense Politeness:** The audit protocol strictly commands agents **never** to attempt cracking or bypassing CAPTCHAs/Cloudflare Turnstile gates. If a verification challenge is detected, the audit terminates and logs the event in `report.md`.
- **Domain Confinement:** External and third-party links are captured in `connections.md` without triggering outbound navigation, safeguarding the audit boundary.
