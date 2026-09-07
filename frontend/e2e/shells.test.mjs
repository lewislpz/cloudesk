import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { once } from "node:events";
import process from "node:process";
import test from "node:test";
import { fileURLToPath } from "node:url";

const frontend = fileURLToPath(new URL("../", import.meta.url));

test(
  "production shells respond over HTTP without exposing configuration",
  { timeout: 30000 },
  async (t) => {
    const marker = "synthetic-server-only-e2e-marker";
    const server = spawn(
      process.execPath,
      [
        "node_modules/next/dist/bin/next",
        "start",
        "--port",
        "0",
        "--hostname",
        "127.0.0.1",
      ],
      {
        cwd: frontend,
        env: {
          ...process.env,
          NEXT_TELEMETRY_DISABLED: "1",
          CLOUDESK_E2E_PRIVATE: marker,
        },
        stdio: ["ignore", "pipe", "pipe"],
      },
    );
    const exited = once(server, "exit");
    t.after(async () => {
      if (server.exitCode === null && server.signalCode === null)
        server.kill("SIGTERM");
      const killTimer = setTimeout(() => server.kill("SIGKILL"), 5000);
      try {
        await exited;
      } finally {
        clearTimeout(killTimer);
      }
    });
    const origin = await new Promise((resolve, reject) => {
      let output = "";
      const timer = setTimeout(
        () => reject(new Error("web startup exceeded 20 seconds")),
        20000,
      );
      server.once("error", reject);
      exited.then(() => {
        clearTimeout(timer);
        reject(new Error("web exited before readiness"));
      });
      server.stderr.on("data", () => {});
      server.stdout.on("data", (chunk) => {
        output += chunk;
        const url = output.match(/http:\/\/(?:localhost|127\.0\.0\.1):\d+/);
        if (url && output.includes("Ready")) {
          clearTimeout(timer);
          resolve(url[0].replace("localhost", "127.0.0.1"));
        }
      });
    });
    for (const route of ["/", "/onboarding", "/acme-consulting"]) {
      const response = await fetch(`${origin}${route}`, {
        signal: AbortSignal.timeout(5000),
      });
      assert.equal(response.status, 200, route);
      assert.match(response.headers.get("content-type"), /text\/html/);
      const html = await response.text();
      assert.match(html, /ClouDesk/);
      assert.match(html, /<main[\s>]/);
      assert.ok(
        !html.includes(marker),
        "server configuration appeared in HTML",
      );
    }
  },
);
