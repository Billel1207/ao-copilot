#!/usr/bin/env node
/**
 * Deploy Next.js source archive to Hostinger via their API.
 *
 * Replicates the flow of the Hostinger MCP tool:
 *   1. Resolve username from domain
 *   2. Get TUS upload credentials
 *   3. Upload archive via TUS protocol
 *   4. Fetch build settings from archive
 *   5. Trigger Node.js build
 *
 * Usage:
 *   HOSTINGER_API_TOKEN=xxx node scripts/deploy-hostinger.mjs <archive.zip>
 *
 * Environment variables:
 *   HOSTINGER_API_TOKEN  - Hostinger API bearer token (required)
 *   HOSTINGER_DOMAIN     - Domain to deploy to (default: ao-copilot.fr)
 */
import fs from 'fs';
import path from 'path';
import https from 'https';
import http from 'http';

const API_BASE = 'https://developers.hostinger.com';
const DOMAIN = process.env.HOSTINGER_DOMAIN || 'ao-copilot.fr';
const TOKEN = process.env.HOSTINGER_API_TOKEN;
const ARCHIVE_PATH = process.argv[2];

if (!TOKEN) {
  console.error('ERROR: HOSTINGER_API_TOKEN environment variable is required');
  process.exit(1);
}
if (!ARCHIVE_PATH || !fs.existsSync(ARCHIVE_PATH)) {
  console.error(`ERROR: Archive file not found: ${ARCHIVE_PATH}`);
  console.error('Usage: node scripts/deploy-hostinger.mjs <archive.zip>');
  process.exit(1);
}

// ── HTTP helper ─────────────────────────────────────────────────────────────

function apiRequest(method, urlPath, body = null) {
  return new Promise((resolve, reject) => {
    const url = new URL(urlPath, API_BASE);
    const options = {
      method,
      hostname: url.hostname,
      port: url.port || 443,
      path: url.pathname + url.search,
      headers: {
        'Authorization': `Bearer ${TOKEN}`,
        'Accept': 'application/json',
      },
    };
    if (body) {
      const data = JSON.stringify(body);
      options.headers['Content-Type'] = 'application/json';
      options.headers['Content-Length'] = Buffer.byteLength(data);
    }

    const req = https.request(options, (res) => {
      let chunks = [];
      res.on('data', (c) => chunks.push(c));
      res.on('end', () => {
        const raw = Buffer.concat(chunks).toString();
        try {
          const json = JSON.parse(raw);
          if (res.statusCode >= 400) {
            reject(new Error(`API ${res.statusCode}: ${raw}`));
          } else {
            resolve(json);
          }
        } catch {
          if (res.statusCode >= 400) reject(new Error(`API ${res.statusCode}: ${raw}`));
          else resolve(raw);
        }
      });
    });
    req.on('error', reject);
    req.setTimeout(60000, () => { req.destroy(); reject(new Error('Request timeout')); });
    if (body) req.write(JSON.stringify(body));
    req.end();
  });
}

// ── TUS upload (simplified single-chunk for archives < 100MB) ───────────────

function tusUpload(filePath, uploadUrl, authToken, authRestToken) {
  return new Promise((resolve, reject) => {
    const stats = fs.statSync(filePath);
    const fileName = path.basename(filePath);
    const fullUrl = `${uploadUrl.replace(/\/$/, '')}/${fileName}?override=true`;
    const parsedUrl = new URL(fullUrl);

    const transport = parsedUrl.protocol === 'https:' ? https : http;

    // Step 1: POST to create the upload
    const postOptions = {
      method: 'POST',
      hostname: parsedUrl.hostname,
      port: parsedUrl.port || (parsedUrl.protocol === 'https:' ? 443 : 80),
      path: parsedUrl.pathname + parsedUrl.search,
      headers: {
        'X-Auth': authToken,
        'X-Auth-Rest': authRestToken,
        'upload-length': stats.size.toString(),
        'upload-offset': '0',
      },
    };

    console.log(`  POST ${parsedUrl.hostname}${parsedUrl.pathname} (create upload)`);
    const postReq = transport.request(postOptions, (res) => {
      let body = '';
      res.on('data', (c) => body += c);
      res.on('end', () => {
        if (res.statusCode !== 201) {
          reject(new Error(`TUS create failed: ${res.statusCode} ${body}`));
          return;
        }
        // Step 2: PATCH to upload file data
        const patchOptions = {
          method: 'PATCH',
          hostname: parsedUrl.hostname,
          port: parsedUrl.port || (parsedUrl.protocol === 'https:' ? 443 : 80),
          path: parsedUrl.pathname + parsedUrl.search,
          headers: {
            'X-Auth': authToken,
            'X-Auth-Rest': authRestToken,
            'upload-offset': '0',
            'Content-Type': 'application/offset+octet-stream',
            'Content-Length': stats.size.toString(),
          },
        };

        console.log(`  PATCH ${parsedUrl.hostname}${parsedUrl.pathname} (upload ${(stats.size / 1024 / 1024).toFixed(1)} MB)`);
        const patchReq = transport.request(patchOptions, (patchRes) => {
          let pBody = '';
          patchRes.on('data', (c) => pBody += c);
          patchRes.on('end', () => {
            if (patchRes.statusCode >= 200 && patchRes.statusCode < 300) {
              resolve({ filename: fileName });
            } else {
              reject(new Error(`TUS upload failed: ${patchRes.statusCode} ${pBody}`));
            }
          });
        });
        patchReq.on('error', reject);
        patchReq.setTimeout(300000, () => { patchReq.destroy(); reject(new Error('Upload timeout')); });

        const fileStream = fs.createReadStream(filePath);
        fileStream.pipe(patchReq);
      });
    });
    postReq.on('error', reject);
    postReq.setTimeout(60000, () => { postReq.destroy(); reject(new Error('Create timeout')); });
    postReq.end('');
  });
}

// ── Main deploy flow ────────────────────────────────────────────────────────

async function main() {
  const archiveName = path.basename(ARCHIVE_PATH);
  console.log(`\nHostinger Deploy: ${archiveName} -> ${DOMAIN}\n`);

  // 1. Resolve username
  console.log('Step 1/5: Resolving username...');
  const websitesResp = await apiRequest('GET', `/api/hosting/v1/websites?domain=${encodeURIComponent(DOMAIN)}`);
  const username = websitesResp?.data?.[0]?.username;
  if (!username) throw new Error(`No website found for domain: ${DOMAIN}`);
  console.log(`  Username: ${username}`);

  // 2. Get upload credentials
  console.log('Step 2/5: Getting upload credentials...');
  const creds = await apiRequest('POST', '/api/hosting/v1/files/upload-urls', { username, domain: DOMAIN });
  const { url: uploadUrl, auth_key: authToken, rest_auth_key: authRestToken } = creds;
  if (!uploadUrl || !authToken) throw new Error('Invalid upload credentials');
  console.log(`  Upload URL: ${uploadUrl.substring(0, 50)}...`);

  // 3. Upload archive via TUS
  console.log('Step 3/5: Uploading archive...');
  const uploadResult = await tusUpload(ARCHIVE_PATH, uploadUrl, authToken, authRestToken);
  console.log(`  Uploaded: ${uploadResult.filename}`);

  // 4. Fetch build settings
  console.log('Step 4/5: Fetching build settings...');
  let buildSettings;
  try {
    buildSettings = await apiRequest(
      'GET',
      `/api/hosting/v1/accounts/${username}/websites/${DOMAIN}/nodejs/builds/settings/from-archive?archive_path=${encodeURIComponent(archiveName)}`
    );
    console.log(`  Build settings: node ${buildSettings.node_version}, ${buildSettings.app_type}`);
  } catch (err) {
    console.warn(`  Warning: Could not auto-detect settings (${err.message}). Using defaults.`);
    buildSettings = {
      node_version: 20,
      app_type: 'next',
      output_directory: '.next',
      build_script: 'build',
    };
  }

  // 5. Trigger build
  console.log('Step 5/5: Triggering build...');
  const buildData = {
    ...buildSettings,
    node_version: buildSettings.node_version || 20,
    source_type: 'archive',
    source_options: { archive_path: archiveName },
  };
  const buildResp = await apiRequest(
    'POST',
    `/api/hosting/v1/accounts/${username}/websites/${DOMAIN}/nodejs/builds`,
    buildData
  );
  console.log(`  Build triggered successfully!`);
  if (buildResp?.data?.uuid) {
    console.log(`  Build UUID: ${buildResp.data.uuid}`);
  }

  console.log(`\nDeploy complete! Check https://${DOMAIN} in ~2 minutes.\n`);
}

main().catch((err) => {
  console.error(`\nDEPLOY FAILED: ${err.message}\n`);
  process.exit(1);
});
