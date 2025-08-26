const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const os = require('os');
const fs = require('fs');

let mainWindow;
let serverProcess = null;

// Get local IP address
function getLocalIP() {
    const interfaces = os.networkInterfaces();
    for (const name of Object.keys(interfaces)) {
        for (const interface of interfaces[name]) {
            const { address, family, internal } = interface;
            if (family === 'IPv4' && !internal) {
                return address;
            }
        }
    }
    return '127.0.0.1';
}

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 600,
        height: 900,
        minWidth: 500,
        minHeight: 700,
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
            preload: path.join(__dirname, 'preload.js')
        },
        show: false
    });

    mainWindow.loadFile('index.html');
    
    mainWindow.once('ready-to-show', () => {
        mainWindow.show();
        // Auto-open dev tools for debugging
        mainWindow.webContents.openDevTools();
    });

    mainWindow.on('closed', () => {
        if (serverProcess) {
            serverProcess.kill();
        }
        mainWindow = null;
    });
}

// Enhanced server start with detailed logging
ipcMain.handle('start-server', async () => {
    console.log('🚀 START SERVER CALLED');
    
    try {
        if (serverProcess) {
            throw new Error('Server is already running');
        }

        // Path configuration - CORRECTED for your structure
        const projectRoot = path.resolve(__dirname, '..');
        const serverPath = path.join(projectRoot, 'server-side');
        const pythonScript = path.join(serverPath, 'mouse_server.py');
        const virtualEnvPath = path.join(serverPath, 'mouse_env', 'bin', 'activate');
        
        console.log('🔍 Path Debug:');
        console.log('  __dirname:', __dirname);
        console.log('  Project root:', projectRoot);
        console.log('  Server path:', serverPath);
        console.log('  Python script:', pythonScript);
        console.log('  Virtual env:', virtualEnvPath);
        
        // Check if files exist
        const serverExists = fs.existsSync(serverPath);
        const scriptExists = fs.existsSync(pythonScript);
        const venvExists = fs.existsSync(virtualEnvPath);
        
        console.log('🔍 File Check:');
        console.log('  Server directory exists:', serverExists);
        console.log('  Python script exists:', scriptExists);
        console.log('  Virtual env exists:', venvExists);
        
        if (!serverExists) {
            throw new Error(`Server directory not found: ${serverPath}`);
        }
        
        if (!scriptExists) {
            throw new Error(`Python script not found: ${pythonScript}`);
        }
        
        // Try with virtual environment first, fallback to direct python3
        let command, args;
        
        if (venvExists) {
            console.log('🐍 Using virtual environment');
            command = 'bash';
            args = ['-c', `cd "${serverPath}" && source mouse_env/bin/activate && python3 mouse_server.py`];
        } else {
            console.log('🐍 Using direct python3 (no venv found)');
            command = 'python3';
            args = [pythonScript];
        }
        
        console.log('🚀 Spawning process:');
        console.log('  Command:', command);
        console.log('  Args:', JSON.stringify(args));
        console.log('  Working dir:', serverPath);

        serverProcess = spawn(command, args, {
            cwd: serverPath,
            detached: false,
            stdio: ['pipe', 'pipe', 'pipe'],
            shell: false
        });

        console.log('✅ Process spawned with PID:', serverProcess.pid);
        
        const localIP = getLocalIP();

        return new Promise((resolve, reject) => {
            let serverStarted = false;
            let outputReceived = false;
            
            const timeout = setTimeout(() => {
                if (!serverStarted) {
                    console.log('⏱️ Server startup timeout');
                    if (serverProcess) {
                        serverProcess.kill();
                        serverProcess = null;
                    }
                    reject(new Error('Server startup timeout - check console for errors'));
                }
            }, 15000);

            serverProcess.stdout.on('data', (data) => {
                const output = data.toString();
                console.log('📤 STDOUT:', output);
                outputReceived = true;
                
                // Look for server started indicators
                if ((output.includes('Running on') || 
                     output.includes('Server') || 
                     output.includes('8080') ||
                     output.includes('Starting')) && !serverStarted) {
                    
                    console.log('🎉 Server start detected!');
                    serverStarted = true;
                    clearTimeout(timeout);
                    resolve({ 
                        success: true, 
                        ip: localIP,
                        message: 'Server started successfully' 
                    });
                }
                
                // Send logs to UI
                if (mainWindow) {
                    mainWindow.webContents.send('server-log', {
                        type: 'info',
                        message: output.trim()
                    });
                }
            });

            serverProcess.stderr.on('data', (data) => {
                const error = data.toString();
                console.error('📤 STDERR:', error);
                outputReceived = true;
                
                if (mainWindow) {
                    mainWindow.webContents.send('server-log', {
                        type: 'error',
                        message: error.trim()
                    });
                }
                
                // Check for common Python errors
                if (error.includes('ModuleNotFoundError') || 
                    error.includes('ImportError') || 
                    error.includes('command not found')) {
                    clearTimeout(timeout);
                    serverProcess = null;
                    reject(new Error(`Python error: ${error.trim()}`));
                }
            });

            serverProcess.on('error', (error) => {
                console.error('💥 Process spawn error:', error);
                clearTimeout(timeout);
                serverProcess = null;
                if (!serverStarted) {
                    reject(new Error(`Failed to start process: ${error.message}`));
                }
            });

            serverProcess.on('close', (code) => {
                console.log(`📛 Server process exited with code ${code}`);
                clearTimeout(timeout);
                serverProcess = null;
                
                if (mainWindow) {
                    mainWindow.webContents.send('server-stopped');
                }
                
                if (!serverStarted && !outputReceived) {
                    reject(new Error(`Server process exited immediately with code ${code}`));
                }
            });
            
            // Fallback success after 3 seconds if we see any output
            setTimeout(() => {
                if (outputReceived && !serverStarted && serverProcess) {
                    console.log('📈 Assuming server started based on output');
                    serverStarted = true;
                    clearTimeout(timeout);
                    resolve({ 
                        success: true, 
                        ip: localIP,
                        message: 'Server started (output detected)' 
                    });
                }
            }, 3000);
        });

    } catch (error) {
        console.error('💥 Failed to start server:', error);
        if (mainWindow) {
            mainWindow.webContents.send('server-log', {
                type: 'error',
                message: `Startup failed: ${error.message}`
            });
        }
        throw error;
    }
});

ipcMain.handle('stop-server', async () => {
    console.log('🛑 STOP SERVER CALLED');
    try {
        if (!serverProcess) {
            throw new Error('Server is not running');
        }

        serverProcess.kill('SIGTERM');
        
        // Force kill after 5 seconds if still running
        setTimeout(() => {
            if (serverProcess) {
                console.log('🔨 Force killing server process');
                serverProcess.kill('SIGKILL');
                serverProcess = null;
            }
        }, 5000);
        
        serverProcess = null;
        console.log('✅ Server stop signal sent');
        
        return { success: true, message: 'Server stopped successfully' };
    } catch (error) {
        console.error('💥 Failed to stop server:', error);
        throw error;
    }
});

ipcMain.handle('get-local-ip', async () => {
    const ip = getLocalIP();
    console.log('🌐 Local IP requested:', ip);
    return ip;
});

ipcMain.handle('is-server-running', async () => {
    const running = serverProcess !== null;
    console.log('❓ Server running check:', running);
    return running;
});

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        if (serverProcess) {
            serverProcess.kill();
        }
        app.quit();
    }
});

app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
        createWindow();
    }
});

app.on('before-quit', () => {
    if (serverProcess) {
        serverProcess.kill();
    }
});
