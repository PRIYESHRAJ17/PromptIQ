#!/usr/bin/env node
/**
 * PromptIQ Model Context Protocol (MCP) Stdio Runner
 * Spawns the PromptIQ JSON-RPC MCP server with verified environment and dependencies.
 */

const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

const PROMPTIQ_REPO = path.resolve('C:/Users/Priyesh Raj/Desktop/PromptIQ');
const VENV_PYTHON = path.join(PROMPTIQ_REPO, '.venv', 'Scripts', 'python.exe');
const DB_PATH = path.join(PROMPTIQ_REPO, 'promptiq.db');

const pythonBin = fs.existsSync(VENV_PYTHON) ? VENV_PYTHON : 'python';

const env = {
  ...process.env,
  PYTHONPATH: PROMPTIQ_REPO,
  DATABASE_URL: `sqlite+aiosqlite:///${DB_PATH.replace(/\\/g, '/')}`,
  PROMPTIQ_ZERO_PRICE_ENFORCEMENT: 'true',
  PROMPTIQ_MCP_MODE: 'true',
};

const child = spawn(pythonBin, ['-m', 'promptiq.mcp.server', ...process.argv.slice(2)], {
  env,
  stdio: 'inherit',
});

child.on('exit', (code) => {
  process.exit(code || 0);
});

child.on('error', (err) => {
  process.stderr.write(`[promptiq-mcp] Failed to spawn MCP server: ${err.message}\n`);
  process.exit(1);
});
