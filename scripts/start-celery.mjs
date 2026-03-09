/**
 * Node.js launcher for Celery worker (Windows-compatible)
 * Uses the Python venv inside apps/api/.venv
 */
import { spawn } from 'child_process';
import { chdir, cwd } from 'process';
import { fileURLToPath } from 'url';
import { dirname, resolve, join } from 'path';
import { existsSync } from 'fs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const projectRoot = resolve(__dirname, '..');
const apiDir = join(projectRoot, 'apps', 'api');

// Change to the api directory
chdir(apiDir);
console.log(`Working directory: ${cwd()}`);

// Determine Python executable path (try venv first, then system)
const venvPython = join(apiDir, '.venv', 'Scripts', 'python.exe');
const venvPythonUnix = join(apiDir, '.venv', 'bin', 'python');
let pythonExe;

if (existsSync(venvPython)) {
  pythonExe = venvPython;
  console.log('Using venv Python (Windows):', pythonExe);
} else if (existsSync(venvPythonUnix)) {
  pythonExe = venvPythonUnix;
  console.log('Using venv Python (Unix):', pythonExe);
} else {
  pythonExe = process.platform === 'win32' ? 'python' : 'python3';
  console.log('Using system Python:', pythonExe);
}

// Run celery via python -m celery (avoids relying on celery.exe in PATH)
const args = [
  '-m', 'celery',
  '-A', 'app.worker.celery_app',
  'worker',
  '--loglevel=info',
  '--pool=solo',       // Windows-compatible (no multiprocessing semaphores)
  '--concurrency=1'
];

console.log(`Starting: ${pythonExe} ${args.join(' ')}`);

const proc = spawn(pythonExe, args, {
  stdio: 'inherit',
  env: {
    ...process.env,
    PYTHONUNBUFFERED: '1',
    FORKED_BY_MULTIPROCESSING: '1'   // needed on Windows for Celery
  }
});

proc.on('error', (err) => {
  console.error('Failed to start celery:', err.message);
  if (err.code === 'ENOENT') {
    console.error('Python not found. Please install Python 3.12 and run:');
    console.error('  cd apps/api && python -m venv .venv && .venv/Scripts/pip install -r requirements.txt');
  }
  process.exit(1);
});

proc.on('exit', (code) => {
  console.log(`Celery worker exited with code ${code}`);
  process.exit(code ?? 0);
});
