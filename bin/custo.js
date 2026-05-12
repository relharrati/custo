#!/usr/bin/env node

// Custo - npm global CLI wrapper
// Proxies to the Python CLI. Install: npm install -g custo

const { spawn, execSync } = require("child_process");
const path = require("path");
const fs = require("fs");
const os = require("os");
const https = require("https");

const REPO = "relharrati/custo";
const CUSTO_DIR = process.env.CUSTO_DIR || path.join(os.homedir(), ".custo");
const CUSTO_PY = path.join(CUSTO_DIR, "custo");
const CUSTO_BAT = path.join(CUSTO_DIR, "custo.bat");

function findPython() {
  const candidates = process.platform === "win32"
    ? ["py", "python3", "python"]
    : ["python3", "python"];
  for (const cmd of candidates) {
    try {
      execSync(`"${cmd}" --version`, { stdio: "ignore" });
      return cmd;
    } catch {}
  }
  return null;
}

function downloadAndInstall() {
  return new Promise((resolve, reject) => {
    console.log("Downloading Custo...");
    const url = `https://github.com/${REPO}/archive/refs/heads/master.zip`;
    const tmp = path.join(os.tmpdir(), "custo.zip");
    const extractDir = path.join(os.tmpdir(), "custo-extract");
    const file = fs.createWriteStream(tmp);

    https.get(url, (res) => {
      res.pipe(file);
      res.on("end", () => {
        file.close(() => {
          try {
            // Use system unzip or PowerShell on Windows
            if (process.platform === "win32") {
              execSync(
                `powershell -c "Expand-Archive -Path '${tmp}' -DestinationPath '${extractDir}' -Force"`,
                { stdio: "ignore" }
              );
            } else {
              execSync(`unzip -o "${tmp}" -d "${extractDir}"`, { stdio: "ignore" });
            }
            const extracted = fs
              .readdirSync(extractDir)
              .find((f) => f.startsWith("custo-"));
            if (!extracted) throw new Error("Extraction failed");
            // Move to install dir
            if (fs.existsSync(CUSTO_DIR)) {
              fs.rmSync(CUSTO_DIR, { recursive: true });
            }
            fs.renameSync(path.join(extractDir, extracted), CUSTO_DIR);
            // Cleanup
            fs.rmSync(extractDir, { recursive: true });
            fs.rmSync(tmp);
            resolve();
          } catch (e) {
            reject(e);
          }
        });
      });
    }).on("error", reject);
  });
}

async function main() {
  const args = process.argv.slice(2);
  const python = findPython();

  if (!python) {
    console.error("Custo requires Python 3.9+. Install from https://python.org");
    process.exit(1);
  }

  // Check if Custo is installed
  const custoExists = fs.existsSync(CUSTO_DIR) &&
    (fs.existsSync(CUSTO_PY) || fs.existsSync(CUSTO_BAT));

  if (!custoExists) {
    console.log("Custo not found. Installing...");
    try {
      await downloadAndInstall();
      console.log("Installing Python dependencies...");
      execSync(`"${python}" -m pip install pyyaml -q`, { stdio: "ignore" });
      console.log("Running first-time setup...");
      execSync(`"${python}" "${path.join(CUSTO_DIR, "setup", "first_run.py")}"`, {
        stdio: "inherit",
      });
    } catch (e) {
      console.error("Installation failed:", e.message);
      console.error(`Try: git clone https://github.com/${REPO}.git ${CUSTO_DIR}`);
      process.exit(1);
    }
  }

  // Proxy to Python CLI
  const custoEntry = process.platform === "win32"
    ? `"${python}" "${CUSTO_BAT}"`
    : `"${python}" "${CUSTO_PY}"`;

  const cliPath = path.join(CUSTO_DIR, "custo");

  const child = spawn(python, [cliPath, ...args], {
    cwd: CUSTO_DIR,
    stdio: "inherit",
    env: { ...process.env, PYTHONPATH: CUSTO_DIR },
  });

  child.on("exit", (code) => process.exit(code));
}

main().catch((e) => {
  console.error("Custo error:", e.message);
  process.exit(1);
});
