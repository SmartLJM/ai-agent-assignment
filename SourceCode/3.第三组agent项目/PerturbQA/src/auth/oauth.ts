/**
 * Anthropic OAuth 2.0 + PKCE flow for PerturbQA.
 * Directly adapted from Pi (packages/ai/src/utils/oauth/anthropic.ts).
 *
 * Flow:
 *   1. Generate PKCE verifier + challenge
 *   2. Start local HTTP callback server on port 53692
 *   3. Open browser to claude.ai/oauth/authorize
 *   4. User logs in, is redirected back to localhost
 *   5. Exchange auth code for access_token + refresh_token
 *   6. access_token can be used directly as Anthropic API key
 */

import { createServer } from "http";
import { generatePKCE } from "./pkce.js";
import type { StoredCredentials } from "./credentials.js";

const CLIENT_ID = atob("OWQxYzI1MGEtZTYxYi00NGQ5LTg4ZWQtNTk0NGQxOTYyZjVl");
const AUTHORIZE_URL = "https://claude.ai/oauth/authorize";
const TOKEN_URL = "https://platform.claude.com/v1/oauth/token";
const CALLBACK_PORT = 53692;
const REDIRECT_URI = `http://localhost:${CALLBACK_PORT}/callback`;
const SCOPES = "org:create_api_key user:profile user:inference user:sessions:claude_code user:mcp_servers user:file_upload";

const SUCCESS_HTML = `<!DOCTYPE html><html><body style="font-family:sans-serif;padding:2rem;max-width:500px;margin:auto">
<h2 style="color:#1a7f4b">✓ PerturbQA Authorized</h2>
<p>Authentication successful. You can close this window and return to the terminal.</p>
</body></html>`;

const ERROR_HTML = (msg: string) => `<!DOCTYPE html><html><body style="font-family:sans-serif;padding:2rem;max-width:500px;margin:auto">
<h2 style="color:#c0392b">✗ Authorization Failed</h2><p>${msg}</p></body></html>`;

async function waitForCallback(expectedState: string): Promise<{ code: string; state: string }> {
  return new Promise((resolve, reject) => {
    const server = createServer((req, res) => {
      const url = new URL(req.url ?? "", "http://localhost");
      if (url.pathname !== "/callback") {
        res.writeHead(404).end();
        return;
      }

      const code = url.searchParams.get("code");
      const state = url.searchParams.get("state");
      const error = url.searchParams.get("error");

      if (error || !code || !state) {
        res.writeHead(400, { "Content-Type": "text/html" }).end(ERROR_HTML(error ?? "Missing code or state"));
        server.close();
        reject(new Error(`OAuth error: ${error ?? "missing parameters"}`));
        return;
      }

      if (state !== expectedState) {
        res.writeHead(400, { "Content-Type": "text/html" }).end(ERROR_HTML("State mismatch"));
        server.close();
        reject(new Error("OAuth state mismatch"));
        return;
      }

      res.writeHead(200, { "Content-Type": "text/html" }).end(SUCCESS_HTML);
      server.close();
      resolve({ code, state });
    });

    server.on("error", (err) => reject(new Error(`Callback server error: ${err.message}`)));
    server.listen(CALLBACK_PORT, "127.0.0.1");
  });
}

async function exchangeCode(code: string, verifier: string): Promise<StoredCredentials> {
  const res = await fetch(TOKEN_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify({
      grant_type: "authorization_code",
      client_id: CLIENT_ID,
      code,
      redirect_uri: REDIRECT_URI,
      code_verifier: verifier,
      state: verifier,
    }),
    signal: AbortSignal.timeout(30_000),
  });

  if (!res.ok) throw new Error(`Token exchange failed: ${res.status} ${await res.text()}`);

  const data = (await res.json()) as { access_token: string; refresh_token: string; expires_in: number };
  return {
    accessToken: data.access_token,
    refreshToken: data.refresh_token,
    expiresAt: Date.now() + data.expires_in * 1000 - 5 * 60 * 1000,
  };
}

export async function refreshToken(refreshTok: string): Promise<StoredCredentials> {
  const res = await fetch(TOKEN_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify({
      grant_type: "refresh_token",
      client_id: CLIENT_ID,
      refresh_token: refreshTok,
    }),
    signal: AbortSignal.timeout(30_000),
  });

  if (!res.ok) throw new Error(`Token refresh failed: ${res.status}`);

  const data = (await res.json()) as { access_token: string; refresh_token: string; expires_in: number };
  return {
    accessToken: data.access_token,
    refreshToken: data.refresh_token,
    expiresAt: Date.now() + data.expires_in * 1000 - 5 * 60 * 1000,
  };
}

export async function loginWithBrowser(
  onUrl: (url: string) => void,
  openBrowser?: (url: string) => void
): Promise<StoredCredentials> {
  const { verifier, challenge } = await generatePKCE();

  const params = new URLSearchParams({
    code: "true",
    client_id: CLIENT_ID,
    response_type: "code",
    redirect_uri: REDIRECT_URI,
    scope: SCOPES,
    code_challenge: challenge,
    code_challenge_method: "S256",
    state: verifier,
  });

  const authUrl = `${AUTHORIZE_URL}?${params.toString()}`;
  onUrl(authUrl);

  if (openBrowser) {
    openBrowser(authUrl);
  }

  const { code } = await waitForCallback(verifier);
  return exchangeCode(code, verifier);
}
