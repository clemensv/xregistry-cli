import * as vscode from 'vscode';
import { exec } from 'child_process';
import * as fs from 'fs';
import * as path from 'path';

const currentVersionMajor = 0;
const currentVersionMinor = 13;
const currentVersionPatch = 0;

async function checkXRegistryTool(context: vscode.ExtensionContext, outputChannel: vscode.OutputChannel): Promise<boolean> {
    try {
        const toolAvailable = await execShellCommand('xregistry --help')
            .then(async (output: string) => {
                outputChannel.appendLine('xregistry CLI found');
                return true;
            })
            .catch(async (error) => {
                const installOption = await vscode.window.showWarningMessage(
                    'xregistry CLI is not available. Do you want to install it?', 'Yes', 'No');
                if (installOption === 'Yes') {
                    if (!await isPythonAvailable()) {
                        const downloadOption = await vscode.window.showErrorMessage('Python 3.10 or higher must be installed. Do you want to open the download page?', 'Yes', 'No');
                        if (downloadOption === 'Yes') {
                            vscode.env.openExternal(vscode.Uri.parse('https://www.python.org/downloads/'));
                        }
                        return false;
                    }
                    outputChannel.show(true);
                    outputChannel.appendLine('Installing xregistry CLI...');
                    await execShellCommand('pip install xregistry', outputChannel);
                    vscode.window.showInformationMessage('xregistry CLI has been installed successfully.');
                    return true;
                }
                return false;
            });
        return toolAvailable;
    } catch (error) {
        vscode.window.showErrorMessage('Error checking xregistry CLI availability: ' + error);
        return false;
    }
}

async function isPythonAvailable(): Promise<boolean> {
    try {
        const output = await execShellCommand('python --version');
        const version = output.trim().split(' ')[1];
        const [major, minor] = version.split('.').map(num => parseInt(num));
        if (major < 3 || (major === 3 && minor < 10)) {
            vscode.window.showInformationMessage('Python 3.10 or higher must be installed. Found version: ' + version);
            return false;
        }
        return major === 3 && minor >= 10;
    } catch {
        return false;
    }
}

function execShellCommand(cmd: string, outputChannel?: vscode.OutputChannel): Promise<string> {
    return new Promise((resolve, reject) => {
        const process = exec(cmd, (error, stdout, stderr) => {
            if (error) {
                reject(error);
            } else {
                resolve(stdout ? stdout : stderr);
            }
        });
        if (outputChannel) {
            process.stdout?.on('data', (data) => {
                outputChannel.append(data.toString());
            });
            process.stderr?.on('data', (data) => {
                outputChannel.append(data.toString());
            });
        }
    });
}

function executeCommand(command: string, outputPath: vscode.Uri | null, outputChannel: vscode.OutputChannel) {
    outputChannel.appendLine(`Executing: ${command}`);
    exec(command, (error, stdout, stderr) => {
        if (error) {
            outputChannel.appendLine(`Error: ${error.message}`);
            vscode.window.showErrorMessage(`Error: ${stderr}`);
        } else {
            outputChannel.appendLine(stdout);
            if (outputPath) {
                if (fs.existsSync(outputPath.fsPath)) {
                    const stats = fs.statSync(outputPath.fsPath);
                    if (stats.isFile()) {
                        vscode.workspace.openTextDocument(outputPath).then((document) => {
                            vscode.window.showTextDocument(document);
                        });
                    } else if (stats.isDirectory()) {
                        vscode.commands.executeCommand('vscode.openFolder', vscode.Uri.file(outputPath.fsPath), true);
                    }
                }
            } else {
                vscode.workspace.openTextDocument({ content: stdout }).then((document) => {
                    vscode.window.showTextDocument(document);
                });
            }
            vscode.window.showInformationMessage('Code generation completed successfully!');
        }
    });
}

function getSuggestedOutputPath(inputFilePath: string, template: string): string {
    const fileBaseName = path.basename(inputFilePath, path.extname(inputFilePath));
    const directory = path.dirname(inputFilePath);
    const suggested = template.replace('{input_file_name}', fileBaseName);
    return path.join(directory, suggested);
}

export function activate(context: vscode.ExtensionContext) {
    const disposables: vscode.Disposable[] = [];
    const outputChannel = vscode.window.createOutputChannel('xregistry');

    disposables.push(vscode.commands.registerCommand('xregistry.generate-py-amqpconsumer', async (uri: vscode.Uri) => {
        const filePath = uri.fsPath;
        
        // Only process .xreg.json files
        if (!filePath.endsWith('.xreg.json')) {
            vscode.window.showWarningMessage('This command requires a .xreg.json file');
            return;
        }
        
        // Ask for project name (mandatory)
        const fileBaseName = path.basename(filePath, path.extname(filePath));
        const projectName = await vscode.window.showInputBox({ 
            prompt: 'Enter project name',
            value: fileBaseName,
            validateInput: (value) => {
                return value && value.trim().length > 0 ? null : 'Project name is required';
            }
        });
        if (!projectName) { return; }
        
        // Ask for output directory (mandatory)
        const outputPathSuggestion = path.join(path.dirname(filePath), '{input_file_name}-py-amqpconsumer'.replace('{input_file_name}', fileBaseName));
        const outputPath = await vscode.window.showOpenDialog({ 
            defaultUri: vscode.Uri.file(outputPathSuggestion), 
            canSelectFiles: false,
            canSelectFolders: true,
            canSelectMany: false,
            openLabel: 'Select Output Directory',
            title: 'Select Output Directory for Generated Code'
        });
        if (!outputPath || outputPath.length === 0) { return; }
        
        // Check if xregistry tool is available
        if (!await checkXRegistryTool(context, outputChannel)) { return; }
        
        const outputDir = outputPath[0].fsPath;
                const command = `xregistry generate --language py --style amqpconsumer --definitions "${filePath}" --output "${outputDir}" --projectname "${projectName}"`; 
        executeCommand(command, outputPath[0], outputChannel);
    }));
    disposables.push(vscode.commands.registerCommand('xregistry.generate-py-amqpproducer', async (uri: vscode.Uri) => {
        const filePath = uri.fsPath;
        
        // Only process .xreg.json files
        if (!filePath.endsWith('.xreg.json')) {
            vscode.window.showWarningMessage('This command requires a .xreg.json file');
            return;
        }
        
        // Ask for project name (mandatory)
        const fileBaseName = path.basename(filePath, path.extname(filePath));
        const projectName = await vscode.window.showInputBox({ 
            prompt: 'Enter project name',
            value: fileBaseName,
            validateInput: (value) => {
                return value && value.trim().length > 0 ? null : 'Project name is required';
            }
        });
        if (!projectName) { return; }
        
        // Ask for output directory (mandatory)
        const outputPathSuggestion = path.join(path.dirname(filePath), '{input_file_name}-py-amqpproducer'.replace('{input_file_name}', fileBaseName));
        const outputPath = await vscode.window.showOpenDialog({ 
            defaultUri: vscode.Uri.file(outputPathSuggestion), 
            canSelectFiles: false,
            canSelectFolders: true,
            canSelectMany: false,
            openLabel: 'Select Output Directory',
            title: 'Select Output Directory for Generated Code'
        });
        if (!outputPath || outputPath.length === 0) { return; }
        
        // Check if xregistry tool is available
        if (!await checkXRegistryTool(context, outputChannel)) { return; }
        
        const outputDir = outputPath[0].fsPath;
                const command = `xregistry generate --language py --style amqpproducer --definitions "${filePath}" --output "${outputDir}" --projectname "${projectName}"`; 
        executeCommand(command, outputPath[0], outputChannel);
    }));
    disposables.push(vscode.commands.registerCommand('xregistry.generate-py-ehconsumer', async (uri: vscode.Uri) => {
        const filePath = uri.fsPath;
        
        // Only process .xreg.json files
        if (!filePath.endsWith('.xreg.json')) {
            vscode.window.showWarningMessage('This command requires a .xreg.json file');
            return;
        }
        
        // Ask for project name (mandatory)
        const fileBaseName = path.basename(filePath, path.extname(filePath));
        const projectName = await vscode.window.showInputBox({ 
            prompt: 'Enter project name',
            value: fileBaseName,
            validateInput: (value) => {
                return value && value.trim().length > 0 ? null : 'Project name is required';
            }
        });
        if (!projectName) { return; }
        
        // Ask for output directory (mandatory)
        const outputPathSuggestion = path.join(path.dirname(filePath), '{input_file_name}-py-ehconsumer'.replace('{input_file_name}', fileBaseName));
        const outputPath = await vscode.window.showOpenDialog({ 
            defaultUri: vscode.Uri.file(outputPathSuggestion), 
            canSelectFiles: false,
            canSelectFolders: true,
            canSelectMany: false,
            openLabel: 'Select Output Directory',
            title: 'Select Output Directory for Generated Code'
        });
        if (!outputPath || outputPath.length === 0) { return; }
        
        // Check if xregistry tool is available
        if (!await checkXRegistryTool(context, outputChannel)) { return; }
        
        const outputDir = outputPath[0].fsPath;
                const command = `xregistry generate --language py --style ehconsumer --definitions "${filePath}" --output "${outputDir}" --projectname "${projectName}"`; 
        executeCommand(command, outputPath[0], outputChannel);
    }));
    disposables.push(vscode.commands.registerCommand('xregistry.generate-py-ehproducer', async (uri: vscode.Uri) => {
        const filePath = uri.fsPath;
        
        // Only process .xreg.json files
        if (!filePath.endsWith('.xreg.json')) {
            vscode.window.showWarningMessage('This command requires a .xreg.json file');
            return;
        }
        
        // Ask for project name (mandatory)
        const fileBaseName = path.basename(filePath, path.extname(filePath));
        const projectName = await vscode.window.showInputBox({ 
            prompt: 'Enter project name',
            value: fileBaseName,
            validateInput: (value) => {
                return value && value.trim().length > 0 ? null : 'Project name is required';
            }
        });
        if (!projectName) { return; }
        
        // Ask for output directory (mandatory)
        const outputPathSuggestion = path.join(path.dirname(filePath), '{input_file_name}-py-ehproducer'.replace('{input_file_name}', fileBaseName));
        const outputPath = await vscode.window.showOpenDialog({ 
            defaultUri: vscode.Uri.file(outputPathSuggestion), 
            canSelectFiles: false,
            canSelectFolders: true,
            canSelectMany: false,
            openLabel: 'Select Output Directory',
            title: 'Select Output Directory for Generated Code'
        });
        if (!outputPath || outputPath.length === 0) { return; }
        
        // Check if xregistry tool is available
        if (!await checkXRegistryTool(context, outputChannel)) { return; }
        
        const outputDir = outputPath[0].fsPath;
                const command = `xregistry generate --language py --style ehproducer --definitions "${filePath}" --output "${outputDir}" --projectname "${projectName}"`; 
        executeCommand(command, outputPath[0], outputChannel);
    }));
    disposables.push(vscode.commands.registerCommand('xregistry.generate-py-kafkaconsumer', async (uri: vscode.Uri) => {
        const filePath = uri.fsPath;
        
        // Only process .xreg.json files
        if (!filePath.endsWith('.xreg.json')) {
            vscode.window.showWarningMessage('This command requires a .xreg.json file');
            return;
        }
        
        // Ask for project name (mandatory)
        const fileBaseName = path.basename(filePath, path.extname(filePath));
        const projectName = await vscode.window.showInputBox({ 
            prompt: 'Enter project name',
            value: fileBaseName,
            validateInput: (value) => {
                return value && value.trim().length > 0 ? null : 'Project name is required';
            }
        });
        if (!projectName) { return; }
        
        // Ask for output directory (mandatory)
        const outputPathSuggestion = path.join(path.dirname(filePath), '{input_file_name}-py-kafkaconsumer'.replace('{input_file_name}', fileBaseName));
        const outputPath = await vscode.window.showOpenDialog({ 
            defaultUri: vscode.Uri.file(outputPathSuggestion), 
            canSelectFiles: false,
            canSelectFolders: true,
            canSelectMany: false,
            openLabel: 'Select Output Directory',
            title: 'Select Output Directory for Generated Code'
        });
        if (!outputPath || outputPath.length === 0) { return; }
        
        // Check if xregistry tool is available
        if (!await checkXRegistryTool(context, outputChannel)) { return; }
        
        const outputDir = outputPath[0].fsPath;
                const command = `xregistry generate --language py --style kafkaconsumer --definitions "${filePath}" --output "${outputDir}" --projectname "${projectName}"`; 
        executeCommand(command, outputPath[0], outputChannel);
    }));
    disposables.push(vscode.commands.registerCommand('xregistry.generate-py-kafkaproducer', async (uri: vscode.Uri) => {
        const filePath = uri.fsPath;
        
        // Only process .xreg.json files
        if (!filePath.endsWith('.xreg.json')) {
            vscode.window.showWarningMessage('This command requires a .xreg.json file');
            return;
        }
        
        // Ask for project name (mandatory)
        const fileBaseName = path.basename(filePath, path.extname(filePath));
        const projectName = await vscode.window.showInputBox({ 
            prompt: 'Enter project name',
            value: fileBaseName,
            validateInput: (value) => {
                return value && value.trim().length > 0 ? null : 'Project name is required';
            }
        });
        if (!projectName) { return; }
        
        // Ask for output directory (mandatory)
        const outputPathSuggestion = path.join(path.dirname(filePath), '{input_file_name}-py-kafkaproducer'.replace('{input_file_name}', fileBaseName));
        const outputPath = await vscode.window.showOpenDialog({ 
            defaultUri: vscode.Uri.file(outputPathSuggestion), 
            canSelectFiles: false,
            canSelectFolders: true,
            canSelectMany: false,
            openLabel: 'Select Output Directory',
            title: 'Select Output Directory for Generated Code'
        });
        if (!outputPath || outputPath.length === 0) { return; }
        
        // Check if xregistry tool is available
        if (!await checkXRegistryTool(context, outputChannel)) { return; }
        
        const outputDir = outputPath[0].fsPath;
                const command = `xregistry generate --language py --style kafkaproducer --definitions "${filePath}" --output "${outputDir}" --projectname "${projectName}"`; 
        executeCommand(command, outputPath[0], outputChannel);
    }));
    disposables.push(vscode.commands.registerCommand('xregistry.generate-py-mqttclient', async (uri: vscode.Uri) => {
        const filePath = uri.fsPath;
        
        // Only process .xreg.json files
        if (!filePath.endsWith('.xreg.json')) {
            vscode.window.showWarningMessage('This command requires a .xreg.json file');
            return;
        }
        
        // Ask for project name (mandatory)
        const fileBaseName = path.basename(filePath, path.extname(filePath));
        const projectName = await vscode.window.showInputBox({ 
            prompt: 'Enter project name',
            value: fileBaseName,
            validateInput: (value) => {
                return value && value.trim().length > 0 ? null : 'Project name is required';
            }
        });
        if (!projectName) { return; }
        
        // Ask for output directory (mandatory)
        const outputPathSuggestion = path.join(path.dirname(filePath), '{input_file_name}-py-mqttclient'.replace('{input_file_name}', fileBaseName));
        const outputPath = await vscode.window.showOpenDialog({ 
            defaultUri: vscode.Uri.file(outputPathSuggestion), 
            canSelectFiles: false,
            canSelectFolders: true,
            canSelectMany: false,
            openLabel: 'Select Output Directory',
            title: 'Select Output Directory for Generated Code'
        });
        if (!outputPath || outputPath.length === 0) { return; }
        
        // Check if xregistry tool is available
        if (!await checkXRegistryTool(context, outputChannel)) { return; }
        
        const outputDir = outputPath[0].fsPath;
                const command = `xregistry generate --language py --style mqttclient --definitions "${filePath}" --output "${outputDir}" --projectname "${projectName}"`; 
        executeCommand(command, outputPath[0], outputChannel);
    }));
    disposables.push(vscode.commands.registerCommand('xregistry.generate-py-sbconsumer', async (uri: vscode.Uri) => {
        const filePath = uri.fsPath;
        
        // Only process .xreg.json files
        if (!filePath.endsWith('.xreg.json')) {
            vscode.window.showWarningMessage('This command requires a .xreg.json file');
            return;
        }
        
        // Ask for project name (mandatory)
        const fileBaseName = path.basename(filePath, path.extname(filePath));
        const projectName = await vscode.window.showInputBox({ 
            prompt: 'Enter project name',
            value: fileBaseName,
            validateInput: (value) => {
                return value && value.trim().length > 0 ? null : 'Project name is required';
            }
        });
        if (!projectName) { return; }
        
        // Ask for output directory (mandatory)
        const outputPathSuggestion = path.join(path.dirname(filePath), '{input_file_name}-py-sbconsumer'.replace('{input_file_name}', fileBaseName));
        const outputPath = await vscode.window.showOpenDialog({ 
            defaultUri: vscode.Uri.file(outputPathSuggestion), 
            canSelectFiles: false,
            canSelectFolders: true,
            canSelectMany: false,
            openLabel: 'Select Output Directory',
            title: 'Select Output Directory for Generated Code'
        });
        if (!outputPath || outputPath.length === 0) { return; }
        
        // Check if xregistry tool is available
        if (!await checkXRegistryTool(context, outputChannel)) { return; }
        
        const outputDir = outputPath[0].fsPath;
                const command = `xregistry generate --language py --style sbconsumer --definitions "${filePath}" --output "${outputDir}" --projectname "${projectName}"`; 
        executeCommand(command, outputPath[0], outputChannel);
    }));
    disposables.push(vscode.commands.registerCommand('xregistry.generate-py-sbproducer', async (uri: vscode.Uri) => {
        const filePath = uri.fsPath;
        
        // Only process .xreg.json files
        if (!filePath.endsWith('.xreg.json')) {
            vscode.window.showWarningMessage('This command requires a .xreg.json file');
            return;
        }
        
        // Ask for project name (mandatory)
        const fileBaseName = path.basename(filePath, path.extname(filePath));
        const projectName = await vscode.window.showInputBox({ 
            prompt: 'Enter project name',
            value: fileBaseName,
            validateInput: (value) => {
                return value && value.trim().length > 0 ? null : 'Project name is required';
            }
        });
        if (!projectName) { return; }
        
        // Ask for output directory (mandatory)
        const outputPathSuggestion = path.join(path.dirname(filePath), '{input_file_name}-py-sbproducer'.replace('{input_file_name}', fileBaseName));
        const outputPath = await vscode.window.showOpenDialog({ 
            defaultUri: vscode.Uri.file(outputPathSuggestion), 
            canSelectFiles: false,
            canSelectFolders: true,
            canSelectMany: false,
            openLabel: 'Select Output Directory',
            title: 'Select Output Directory for Generated Code'
        });
        if (!outputPath || outputPath.length === 0) { return; }
        
        // Check if xregistry tool is available
        if (!await checkXRegistryTool(context, outputChannel)) { return; }
        
        const outputDir = outputPath[0].fsPath;
                const command = `xregistry generate --language py --style sbproducer --definitions "${filePath}" --output "${outputDir}" --projectname "${projectName}"`; 
        executeCommand(command, outputPath[0], outputChannel);
    }));
    disposables.push(vscode.commands.registerCommand('xregistry.generate-ts-amqpconsumer', async (uri: vscode.Uri) => {
        const filePath = uri.fsPath;
        
        // Only process .xreg.json files
        if (!filePath.endsWith('.xreg.json')) {
            vscode.window.showWarningMessage('This command requires a .xreg.json file');
            return;
        }
        
        // Ask for project name (mandatory)
        const fileBaseName = path.basename(filePath, path.extname(filePath));
        const projectName = await vscode.window.showInputBox({ 
            prompt: 'Enter project name',
            value: fileBaseName,
            validateInput: (value) => {
                return value && value.trim().length > 0 ? null : 'Project name is required';
            }
        });
        if (!projectName) { return; }
        
        // Ask for output directory (mandatory)
        const outputPathSuggestion = path.join(path.dirname(filePath), '{input_file_name}-ts-amqpconsumer'.replace('{input_file_name}', fileBaseName));
        const outputPath = await vscode.window.showOpenDialog({ 
            defaultUri: vscode.Uri.file(outputPathSuggestion), 
            canSelectFiles: false,
            canSelectFolders: true,
            canSelectMany: false,
            openLabel: 'Select Output Directory',
            title: 'Select Output Directory for Generated Code'
        });
        if (!outputPath || outputPath.length === 0) { return; }
        
        // Check if xregistry tool is available
        if (!await checkXRegistryTool(context, outputChannel)) { return; }
        
        const outputDir = outputPath[0].fsPath;
                const command = `xregistry generate --language ts --style amqpconsumer --definitions "${filePath}" --output "${outputDir}" --projectname "${projectName}"`; 
        executeCommand(command, outputPath[0], outputChannel);
    }));
    disposables.push(vscode.commands.registerCommand('xregistry.generate-ts-amqpproducer', async (uri: vscode.Uri) => {
        const filePath = uri.fsPath;
        
        // Only process .xreg.json files
        if (!filePath.endsWith('.xreg.json')) {
            vscode.window.showWarningMessage('This command requires a .xreg.json file');
            return;
        }
        
        // Ask for project name (mandatory)
        const fileBaseName = path.basename(filePath, path.extname(filePath));
        const projectName = await vscode.window.showInputBox({ 
            prompt: 'Enter project name',
            value: fileBaseName,
            validateInput: (value) => {
                return value && value.trim().length > 0 ? null : 'Project name is required';
            }
        });
        if (!projectName) { return; }
        
        // Ask for output directory (mandatory)
        const outputPathSuggestion = path.join(path.dirname(filePath), '{input_file_name}-ts-amqpproducer'.replace('{input_file_name}', fileBaseName));
        const outputPath = await vscode.window.showOpenDialog({ 
            defaultUri: vscode.Uri.file(outputPathSuggestion), 
            canSelectFiles: false,
            canSelectFolders: true,
            canSelectMany: false,
            openLabel: 'Select Output Directory',
            title: 'Select Output Directory for Generated Code'
        });
        if (!outputPath || outputPath.length === 0) { return; }
        
        // Check if xregistry tool is available
        if (!await checkXRegistryTool(context, outputChannel)) { return; }
        
        const outputDir = outputPath[0].fsPath;
                const command = `xregistry generate --language ts --style amqpproducer --definitions "${filePath}" --output "${outputDir}" --projectname "${projectName}"`; 
        executeCommand(command, outputPath[0], outputChannel);
    }));
    disposables.push(vscode.commands.registerCommand('xregistry.generate-ts-egproducer', async (uri: vscode.Uri) => {
        const filePath = uri.fsPath;
        
        // Only process .xreg.json files
        if (!filePath.endsWith('.xreg.json')) {
            vscode.window.showWarningMessage('This command requires a .xreg.json file');
            return;
        }
        
        // Ask for project name (mandatory)
        const fileBaseName = path.basename(filePath, path.extname(filePath));
        const projectName = await vscode.window.showInputBox({ 
            prompt: 'Enter project name',
            value: fileBaseName,
            validateInput: (value) => {
                return value && value.trim().length > 0 ? null : 'Project name is required';
            }
        });
        if (!projectName) { return; }
        
        // Ask for output directory (mandatory)
        const outputPathSuggestion = path.join(path.dirname(filePath), '{input_file_name}-ts-egproducer'.replace('{input_file_name}', fileBaseName));
        const outputPath = await vscode.window.showOpenDialog({ 
            defaultUri: vscode.Uri.file(outputPathSuggestion), 
            canSelectFiles: false,
            canSelectFolders: true,
            canSelectMany: false,
            openLabel: 'Select Output Directory',
            title: 'Select Output Directory for Generated Code'
        });
        if (!outputPath || outputPath.length === 0) { return; }
        
        // Check if xregistry tool is available
        if (!await checkXRegistryTool(context, outputChannel)) { return; }
        
        const outputDir = outputPath[0].fsPath;
                const command = `xregistry generate --language ts --style egproducer --definitions "${filePath}" --output "${outputDir}" --projectname "${projectName}"`; 
        executeCommand(command, outputPath[0], outputChannel);
    }));
    disposables.push(vscode.commands.registerCommand('xregistry.generate-ts-ehproducer', async (uri: vscode.Uri) => {
        const filePath = uri.fsPath;
        
        // Only process .xreg.json files
        if (!filePath.endsWith('.xreg.json')) {
            vscode.window.showWarningMessage('This command requires a .xreg.json file');
            return;
        }
        
        // Ask for project name (mandatory)
        const fileBaseName = path.basename(filePath, path.extname(filePath));
        const projectName = await vscode.window.showInputBox({ 
            prompt: 'Enter project name',
            value: fileBaseName,
            validateInput: (value) => {
                return value && value.trim().length > 0 ? null : 'Project name is required';
            }
        });
        if (!projectName) { return; }
        
        // Ask for output directory (mandatory)
        const outputPathSuggestion = path.join(path.dirname(filePath), '{input_file_name}-ts-ehproducer'.replace('{input_file_name}', fileBaseName));
        const outputPath = await vscode.window.showOpenDialog({ 
            defaultUri: vscode.Uri.file(outputPathSuggestion), 
            canSelectFiles: false,
            canSelectFolders: true,
            canSelectMany: false,
            openLabel: 'Select Output Directory',
            title: 'Select Output Directory for Generated Code'
        });
        if (!outputPath || outputPath.length === 0) { return; }
        
        // Check if xregistry tool is available
        if (!await checkXRegistryTool(context, outputChannel)) { return; }
        
        const outputDir = outputPath[0].fsPath;
                const command = `xregistry generate --language ts --style ehproducer --definitions "${filePath}" --output "${outputDir}" --projectname "${projectName}"`; 
        executeCommand(command, outputPath[0], outputChannel);
    }));
    disposables.push(vscode.commands.registerCommand('xregistry.generate-ts-mqttclient', async (uri: vscode.Uri) => {
        const filePath = uri.fsPath;
        
        // Only process .xreg.json files
        if (!filePath.endsWith('.xreg.json')) {
            vscode.window.showWarningMessage('This command requires a .xreg.json file');
            return;
        }
        
        // Ask for project name (mandatory)
        const fileBaseName = path.basename(filePath, path.extname(filePath));
        const projectName = await vscode.window.showInputBox({ 
            prompt: 'Enter project name',
            value: fileBaseName,
            validateInput: (value) => {
                return value && value.trim().length > 0 ? null : 'Project name is required';
            }
        });
        if (!projectName) { return; }
        
        // Ask for output directory (mandatory)
        const outputPathSuggestion = path.join(path.dirname(filePath), '{input_file_name}-ts-mqttclient'.replace('{input_file_name}', fileBaseName));
        const outputPath = await vscode.window.showOpenDialog({ 
            defaultUri: vscode.Uri.file(outputPathSuggestion), 
            canSelectFiles: false,
            canSelectFolders: true,
            canSelectMany: false,
            openLabel: 'Select Output Directory',
            title: 'Select Output Directory for Generated Code'
        });
        if (!outputPath || outputPath.length === 0) { return; }
        
        // Check if xregistry tool is available
        if (!await checkXRegistryTool(context, outputChannel)) { return; }
        
        const outputDir = outputPath[0].fsPath;
                const command = `xregistry generate --language ts --style mqttclient --definitions "${filePath}" --output "${outputDir}" --projectname "${projectName}"`; 
        executeCommand(command, outputPath[0], outputChannel);
    }));
    disposables.push(vscode.commands.registerCommand('xregistry.generate-ts-producerhttp', async (uri: vscode.Uri) => {
        const filePath = uri.fsPath;
        
        // Only process .xreg.json files
        if (!filePath.endsWith('.xreg.json')) {
            vscode.window.showWarningMessage('This command requires a .xreg.json file');
            return;
        }
        
        // Ask for project name (mandatory)
        const fileBaseName = path.basename(filePath, path.extname(filePath));
        const projectName = await vscode.window.showInputBox({ 
            prompt: 'Enter project name',
            value: fileBaseName,
            validateInput: (value) => {
                return value && value.trim().length > 0 ? null : 'Project name is required';
            }
        });
        if (!projectName) { return; }
        
        // Ask for output directory (mandatory)
        const outputPathSuggestion = path.join(path.dirname(filePath), '{input_file_name}-ts-producerhttp'.replace('{input_file_name}', fileBaseName));
        const outputPath = await vscode.window.showOpenDialog({ 
            defaultUri: vscode.Uri.file(outputPathSuggestion), 
            canSelectFiles: false,
            canSelectFolders: true,
            canSelectMany: false,
            openLabel: 'Select Output Directory',
            title: 'Select Output Directory for Generated Code'
        });
        if (!outputPath || outputPath.length === 0) { return; }
        
        // Check if xregistry tool is available
        if (!await checkXRegistryTool(context, outputChannel)) { return; }
        
        const outputDir = outputPath[0].fsPath;
                const command = `xregistry generate --language ts --style producerhttp --definitions "${filePath}" --output "${outputDir}" --projectname "${projectName}"`; 
        executeCommand(command, outputPath[0], outputChannel);
    }));
    disposables.push(vscode.commands.registerCommand('xregistry.generate-ts-sbconsumer', async (uri: vscode.Uri) => {
        const filePath = uri.fsPath;
        
        // Only process .xreg.json files
        if (!filePath.endsWith('.xreg.json')) {
            vscode.window.showWarningMessage('This command requires a .xreg.json file');
            return;
        }
        
        // Ask for project name (mandatory)
        const fileBaseName = path.basename(filePath, path.extname(filePath));
        const projectName = await vscode.window.showInputBox({ 
            prompt: 'Enter project name',
            value: fileBaseName,
            validateInput: (value) => {
                return value && value.trim().length > 0 ? null : 'Project name is required';
            }
        });
        if (!projectName) { return; }
        
        // Ask for output directory (mandatory)
        const outputPathSuggestion = path.join(path.dirname(filePath), '{input_file_name}-ts-sbconsumer'.replace('{input_file_name}', fileBaseName));
        const outputPath = await vscode.window.showOpenDialog({ 
            defaultUri: vscode.Uri.file(outputPathSuggestion), 
            canSelectFiles: false,
            canSelectFolders: true,
            canSelectMany: false,
            openLabel: 'Select Output Directory',
            title: 'Select Output Directory for Generated Code'
        });
        if (!outputPath || outputPath.length === 0) { return; }
        
        // Check if xregistry tool is available
        if (!await checkXRegistryTool(context, outputChannel)) { return; }
        
        const outputDir = outputPath[0].fsPath;
                const command = `xregistry generate --language ts --style sbconsumer --definitions "${filePath}" --output "${outputDir}" --projectname "${projectName}"`; 
        executeCommand(command, outputPath[0], outputChannel);
    }));
    disposables.push(vscode.commands.registerCommand('xregistry.generate-ts-sbproducer', async (uri: vscode.Uri) => {
        const filePath = uri.fsPath;
        
        // Only process .xreg.json files
        if (!filePath.endsWith('.xreg.json')) {
            vscode.window.showWarningMessage('This command requires a .xreg.json file');
            return;
        }
        
        // Ask for project name (mandatory)
        const fileBaseName = path.basename(filePath, path.extname(filePath));
        const projectName = await vscode.window.showInputBox({ 
            prompt: 'Enter project name',
            value: fileBaseName,
            validateInput: (value) => {
                return value && value.trim().length > 0 ? null : 'Project name is required';
            }
        });
        if (!projectName) { return; }
        
        // Ask for output directory (mandatory)
        const outputPathSuggestion = path.join(path.dirname(filePath), '{input_file_name}-ts-sbproducer'.replace('{input_file_name}', fileBaseName));
        const outputPath = await vscode.window.showOpenDialog({ 
            defaultUri: vscode.Uri.file(outputPathSuggestion), 
            canSelectFiles: false,
            canSelectFolders: true,
            canSelectMany: false,
            openLabel: 'Select Output Directory',
            title: 'Select Output Directory for Generated Code'
        });
        if (!outputPath || outputPath.length === 0) { return; }
        
        // Check if xregistry tool is available
        if (!await checkXRegistryTool(context, outputChannel)) { return; }
        
        const outputDir = outputPath[0].fsPath;
                const command = `xregistry generate --language ts --style sbproducer --definitions "${filePath}" --output "${outputDir}" --projectname "${projectName}"`; 
        executeCommand(command, outputPath[0], outputChannel);
    }));
    disposables.push(vscode.commands.registerCommand('xregistry.generate-ts-dashboard', async (uri: vscode.Uri) => {
        const filePath = uri.fsPath;
        
        // Only process .xreg.json files
        if (!filePath.endsWith('.xreg.json')) {
            vscode.window.showWarningMessage('This command requires a .xreg.json file');
            return;
        }
        
        // Ask for project name (mandatory)
        const fileBaseName = path.basename(filePath, path.extname(filePath));
        const projectName = await vscode.window.showInputBox({ 
            prompt: 'Enter project name',
            value: fileBaseName,
            validateInput: (value) => {
                return value && value.trim().length > 0 ? null : 'Project name is required';
            }
        });
        if (!projectName) { return; }
        
        // Ask for output directory (mandatory)
        const outputPathSuggestion = path.join(path.dirname(filePath), '{input_file_name}-ts-dashboard'.replace('{input_file_name}', fileBaseName));
        const outputPath = await vscode.window.showOpenDialog({ 
            defaultUri: vscode.Uri.file(outputPathSuggestion), 
            canSelectFiles: false,
            canSelectFolders: true,
            canSelectMany: false,
            openLabel: 'Select Output Directory',
            title: 'Select Output Directory for Generated Code'
        });
        if (!outputPath || outputPath.length === 0) { return; }
        
        // Check if xregistry tool is available
        if (!await checkXRegistryTool(context, outputChannel)) { return; }
        
        const outputDir = outputPath[0].fsPath;
                const command = `xregistry generate --language ts --style dashboard --definitions "${filePath}" --output "${outputDir}" --projectname "${projectName}"`; 
        executeCommand(command, outputPath[0], outputChannel);
    }));
    disposables.push(vscode.commands.registerCommand('xregistry.generate-ts-ehconsumer', async (uri: vscode.Uri) => {
        const filePath = uri.fsPath;
        
        // Only process .xreg.json files
        if (!filePath.endsWith('.xreg.json')) {
            vscode.window.showWarningMessage('This command requires a .xreg.json file');
            return;
        }
        
        // Ask for project name (mandatory)
        const fileBaseName = path.basename(filePath, path.extname(filePath));
        const projectName = await vscode.window.showInputBox({ 
            prompt: 'Enter project name',
            value: fileBaseName,
            validateInput: (value) => {
                return value && value.trim().length > 0 ? null : 'Project name is required';
            }
        });
        if (!projectName) { return; }
        
        // Ask for output directory (mandatory)
        const outputPathSuggestion = path.join(path.dirname(filePath), '{input_file_name}-ts-ehconsumer'.replace('{input_file_name}', fileBaseName));
        const outputPath = await vscode.window.showOpenDialog({ 
            defaultUri: vscode.Uri.file(outputPathSuggestion), 
            canSelectFiles: false,
            canSelectFolders: true,
            canSelectMany: false,
            openLabel: 'Select Output Directory',
            title: 'Select Output Directory for Generated Code'
        });
        if (!outputPath || outputPath.length === 0) { return; }
        
        // Check if xregistry tool is available
        if (!await checkXRegistryTool(context, outputChannel)) { return; }
        
        const outputDir = outputPath[0].fsPath;
                const command = `xregistry generate --language ts --style ehconsumer --definitions "${filePath}" --output "${outputDir}" --projectname "${projectName}"`; 
        executeCommand(command, outputPath[0], outputChannel);
    }));
    disposables.push(vscode.commands.registerCommand('xregistry.generate-ts-kafkaconsumer', async (uri: vscode.Uri) => {
        const filePath = uri.fsPath;
        
        // Only process .xreg.json files
        if (!filePath.endsWith('.xreg.json')) {
            vscode.window.showWarningMessage('This command requires a .xreg.json file');
            return;
        }
        
        // Ask for project name (mandatory)
        const fileBaseName = path.basename(filePath, path.extname(filePath));
        const projectName = await vscode.window.showInputBox({ 
            prompt: 'Enter project name',
            value: fileBaseName,
            validateInput: (value) => {
                return value && value.trim().length > 0 ? null : 'Project name is required';
            }
        });
        if (!projectName) { return; }
        
        // Ask for output directory (mandatory)
        const outputPathSuggestion = path.join(path.dirname(filePath), '{input_file_name}-ts-kafkaconsumer'.replace('{input_file_name}', fileBaseName));
        const outputPath = await vscode.window.showOpenDialog({ 
            defaultUri: vscode.Uri.file(outputPathSuggestion), 
            canSelectFiles: false,
            canSelectFolders: true,
            canSelectMany: false,
            openLabel: 'Select Output Directory',
            title: 'Select Output Directory for Generated Code'
        });
        if (!outputPath || outputPath.length === 0) { return; }
        
        // Check if xregistry tool is available
        if (!await checkXRegistryTool(context, outputChannel)) { return; }
        
        const outputDir = outputPath[0].fsPath;
                const command = `xregistry generate --language ts --style kafkaconsumer --definitions "${filePath}" --output "${outputDir}" --projectname "${projectName}"`; 
        executeCommand(command, outputPath[0], outputChannel);
    }));
    disposables.push(vscode.commands.registerCommand('xregistry.generate-ts-kafkaproducer', async (uri: vscode.Uri) => {
        const filePath = uri.fsPath;
        
        // Only process .xreg.json files
        if (!filePath.endsWith('.xreg.json')) {
            vscode.window.showWarningMessage('This command requires a .xreg.json file');
            return;
        }
        
        // Ask for project name (mandatory)
        const fileBaseName = path.basename(filePath, path.extname(filePath));
        const projectName = await vscode.window.showInputBox({ 
            prompt: 'Enter project name',
            value: fileBaseName,
            validateInput: (value) => {
                return value && value.trim().length > 0 ? null : 'Project name is required';
            }
        });
        if (!projectName) { return; }
        
        // Ask for output directory (mandatory)
        const outputPathSuggestion = path.join(path.dirname(filePath), '{input_file_name}-ts-kafkaproducer'.replace('{input_file_name}', fileBaseName));
        const outputPath = await vscode.window.showOpenDialog({ 
            defaultUri: vscode.Uri.file(outputPathSuggestion), 
            canSelectFiles: false,
            canSelectFolders: true,
            canSelectMany: false,
            openLabel: 'Select Output Directory',
            title: 'Select Output Directory for Generated Code'
        });
        if (!outputPath || outputPath.length === 0) { return; }
        
        // Check if xregistry tool is available
        if (!await checkXRegistryTool(context, outputChannel)) { return; }
        
        const outputDir = outputPath[0].fsPath;
                const command = `xregistry generate --language ts --style kafkaproducer --definitions "${filePath}" --output "${outputDir}" --projectname "${projectName}"`; 
        executeCommand(command, outputPath[0], outputChannel);
    }));
    disposables.push(vscode.commands.registerCommand('xregistry.generate-java-amqpconsumer', async (uri: vscode.Uri) => {
        const filePath = uri.fsPath;
        
        // Only process .xreg.json files
        if (!filePath.endsWith('.xreg.json')) {
            vscode.window.showWarningMessage('This command requires a .xreg.json file');
            return;
        }
        
        // Ask for project name (mandatory)
        const fileBaseName = path.basename(filePath, path.extname(filePath));
        const projectName = await vscode.window.showInputBox({ 
            prompt: 'Enter project name',
            value: fileBaseName,
            validateInput: (value) => {
                return value && value.trim().length > 0 ? null : 'Project name is required';
            }
        });
        if (!projectName) { return; }
        
        // Ask for output directory (mandatory)
        const outputPathSuggestion = path.join(path.dirname(filePath), '{input_file_name}-java-amqpconsumer'.replace('{input_file_name}', fileBaseName));
        const outputPath = await vscode.window.showOpenDialog({ 
            defaultUri: vscode.Uri.file(outputPathSuggestion), 
            canSelectFiles: false,
            canSelectFolders: true,
            canSelectMany: false,
            openLabel: 'Select Output Directory',
            title: 'Select Output Directory for Generated Code'
        });
        if (!outputPath || outputPath.length === 0) { return; }
        
        // Check if xregistry tool is available
        if (!await checkXRegistryTool(context, outputChannel)) { return; }
        
        const outputDir = outputPath[0].fsPath;
                const command = `xregistry generate --language java --style amqpconsumer --definitions "${filePath}" --output "${outputDir}" --projectname "${projectName}"`; 
        executeCommand(command, outputPath[0], outputChannel);
    }));
    disposables.push(vscode.commands.registerCommand('xregistry.generate-java-amqpjmsproducer', async (uri: vscode.Uri) => {
        const filePath = uri.fsPath;
        
        // Only process .xreg.json files
        if (!filePath.endsWith('.xreg.json')) {
            vscode.window.showWarningMessage('This command requires a .xreg.json file');
            return;
        }
        
        // Ask for project name (mandatory)
        const fileBaseName = path.basename(filePath, path.extname(filePath));
        const projectName = await vscode.window.showInputBox({ 
            prompt: 'Enter project name',
            value: fileBaseName,
            validateInput: (value) => {
                return value && value.trim().length > 0 ? null : 'Project name is required';
            }
        });
        if (!projectName) { return; }
        
        // Ask for output directory (mandatory)
        const outputPathSuggestion = path.join(path.dirname(filePath), '{input_file_name}-java-amqpjmsproducer'.replace('{input_file_name}', fileBaseName));
        const outputPath = await vscode.window.showOpenDialog({ 
            defaultUri: vscode.Uri.file(outputPathSuggestion), 
            canSelectFiles: false,
            canSelectFolders: true,
            canSelectMany: false,
            openLabel: 'Select Output Directory',
            title: 'Select Output Directory for Generated Code'
        });
        if (!outputPath || outputPath.length === 0) { return; }
        
        // Check if xregistry tool is available
        if (!await checkXRegistryTool(context, outputChannel)) { return; }
        
        const outputDir = outputPath[0].fsPath;
                const command = `xregistry generate --language java --style amqpjmsproducer --definitions "${filePath}" --output "${outputDir}" --projectname "${projectName}"`; 
        executeCommand(command, outputPath[0], outputChannel);
    }));
    disposables.push(vscode.commands.registerCommand('xregistry.generate-java-amqpproducer', async (uri: vscode.Uri) => {
        const filePath = uri.fsPath;
        
        // Only process .xreg.json files
        if (!filePath.endsWith('.xreg.json')) {
            vscode.window.showWarningMessage('This command requires a .xreg.json file');
            return;
        }
        
        // Ask for project name (mandatory)
        const fileBaseName = path.basename(filePath, path.extname(filePath));
        const projectName = await vscode.window.showInputBox({ 
            prompt: 'Enter project name',
            value: fileBaseName,
            validateInput: (value) => {
                return value && value.trim().length > 0 ? null : 'Project name is required';
            }
        });
        if (!projectName) { return; }
        
        // Ask for output directory (mandatory)
        const outputPathSuggestion = path.join(path.dirname(filePath), '{input_file_name}-java-amqpproducer'.replace('{input_file_name}', fileBaseName));
        const outputPath = await vscode.window.showOpenDialog({ 
            defaultUri: vscode.Uri.file(outputPathSuggestion), 
            canSelectFiles: false,
            canSelectFolders: true,
            canSelectMany: false,
            openLabel: 'Select Output Directory',
            title: 'Select Output Directory for Generated Code'
        });
        if (!outputPath || outputPath.length === 0) { return; }
        
        // Check if xregistry tool is available
        if (!await checkXRegistryTool(context, outputChannel)) { return; }
        
        const outputDir = outputPath[0].fsPath;
                const command = `xregistry generate --language java --style amqpproducer --definitions "${filePath}" --output "${outputDir}" --projectname "${projectName}"`; 
        executeCommand(command, outputPath[0], outputChannel);
    }));
    disposables.push(vscode.commands.registerCommand('xregistry.generate-java-ehconsumer', async (uri: vscode.Uri) => {
        const filePath = uri.fsPath;
        
        // Only process .xreg.json files
        if (!filePath.endsWith('.xreg.json')) {
            vscode.window.showWarningMessage('This command requires a .xreg.json file');
            return;
        }
        
        // Ask for project name (mandatory)
        const fileBaseName = path.basename(filePath, path.extname(filePath));
        const projectName = await vscode.window.showInputBox({ 
            prompt: 'Enter project name',
            value: fileBaseName,
            validateInput: (value) => {
                return value && value.trim().length > 0 ? null : 'Project name is required';
            }
        });
        if (!projectName) { return; }
        
        // Ask for output directory (mandatory)
        const outputPathSuggestion = path.join(path.dirname(filePath), '{input_file_name}-java-ehconsumer'.replace('{input_file_name}', fileBaseName));
        const outputPath = await vscode.window.showOpenDialog({ 
            defaultUri: vscode.Uri.file(outputPathSuggestion), 
            canSelectFiles: false,
            canSelectFolders: true,
            canSelectMany: false,
            openLabel: 'Select Output Directory',
            title: 'Select Output Directory for Generated Code'
        });
        if (!outputPath || outputPath.length === 0) { return; }
        
        // Check if xregistry tool is available
        if (!await checkXRegistryTool(context, outputChannel)) { return; }
        
        const outputDir = outputPath[0].fsPath;
                const command = `xregistry generate --language java --style ehconsumer --definitions "${filePath}" --output "${outputDir}" --projectname "${projectName}"`; 
        executeCommand(command, outputPath[0], outputChannel);
    }));
    disposables.push(vscode.commands.registerCommand('xregistry.generate-java-ehproducer', async (uri: vscode.Uri) => {
        const filePath = uri.fsPath;
        
        // Only process .xreg.json files
        if (!filePath.endsWith('.xreg.json')) {
            vscode.window.showWarningMessage('This command requires a .xreg.json file');
            return;
        }
        
        // Ask for project name (mandatory)
        const fileBaseName = path.basename(filePath, path.extname(filePath));
        const projectName = await vscode.window.showInputBox({ 
            prompt: 'Enter project name',
            value: fileBaseName,
            validateInput: (value) => {
                return value && value.trim().length > 0 ? null : 'Project name is required';
            }
        });
        if (!projectName) { return; }
        
        // Ask for output directory (mandatory)
        const outputPathSuggestion = path.join(path.dirname(filePath), '{input_file_name}-java-ehproducer'.replace('{input_file_name}', fileBaseName));
        const outputPath = await vscode.window.showOpenDialog({ 
            defaultUri: vscode.Uri.file(outputPathSuggestion), 
            canSelectFiles: false,
            canSelectFolders: true,
            canSelectMany: false,
            openLabel: 'Select Output Directory',
            title: 'Select Output Directory for Generated Code'
        });
        if (!outputPath || outputPath.length === 0) { return; }
        
        // Check if xregistry tool is available
        if (!await checkXRegistryTool(context, outputChannel)) { return; }
        
        const outputDir = outputPath[0].fsPath;
                const command = `xregistry generate --language java --style ehproducer --definitions "${filePath}" --output "${outputDir}" --projectname "${projectName}"`; 
        executeCommand(command, outputPath[0], outputChannel);
    }));
    disposables.push(vscode.commands.registerCommand('xregistry.generate-java-kafkaconsumer', async (uri: vscode.Uri) => {
        const filePath = uri.fsPath;
        
        // Only process .xreg.json files
        if (!filePath.endsWith('.xreg.json')) {
            vscode.window.showWarningMessage('This command requires a .xreg.json file');
            return;
        }
        
        // Ask for project name (mandatory)
        const fileBaseName = path.basename(filePath, path.extname(filePath));
        const projectName = await vscode.window.showInputBox({ 
            prompt: 'Enter project name',
            value: fileBaseName,
            validateInput: (value) => {
                return value && value.trim().length > 0 ? null : 'Project name is required';
            }
        });
        if (!projectName) { return; }
        
        // Ask for output directory (mandatory)
        const outputPathSuggestion = path.join(path.dirname(filePath), '{input_file_name}-java-kafkaconsumer'.replace('{input_file_name}', fileBaseName));
        const outputPath = await vscode.window.showOpenDialog({ 
            defaultUri: vscode.Uri.file(outputPathSuggestion), 
            canSelectFiles: false,
            canSelectFolders: true,
            canSelectMany: false,
            openLabel: 'Select Output Directory',
            title: 'Select Output Directory for Generated Code'
        });
        if (!outputPath || outputPath.length === 0) { return; }
        
        // Check if xregistry tool is available
        if (!await checkXRegistryTool(context, outputChannel)) { return; }
        
        const outputDir = outputPath[0].fsPath;
                const command = `xregistry generate --language java --style kafkaconsumer --definitions "${filePath}" --output "${outputDir}" --projectname "${projectName}"`; 
        executeCommand(command, outputPath[0], outputChannel);
    }));
    disposables.push(vscode.commands.registerCommand('xregistry.generate-java-kafkaproducer', async (uri: vscode.Uri) => {
        const filePath = uri.fsPath;
        
        // Only process .xreg.json files
        if (!filePath.endsWith('.xreg.json')) {
            vscode.window.showWarningMessage('This command requires a .xreg.json file');
            return;
        }
        
        // Ask for project name (mandatory)
        const fileBaseName = path.basename(filePath, path.extname(filePath));
        const projectName = await vscode.window.showInputBox({ 
            prompt: 'Enter project name',
            value: fileBaseName,
            validateInput: (value) => {
                return value && value.trim().length > 0 ? null : 'Project name is required';
            }
        });
        if (!projectName) { return; }
        
        // Ask for output directory (mandatory)
        const outputPathSuggestion = path.join(path.dirname(filePath), '{input_file_name}-java-kafkaproducer'.replace('{input_file_name}', fileBaseName));
        const outputPath = await vscode.window.showOpenDialog({ 
            defaultUri: vscode.Uri.file(outputPathSuggestion), 
            canSelectFiles: false,
            canSelectFolders: true,
            canSelectMany: false,
            openLabel: 'Select Output Directory',
            title: 'Select Output Directory for Generated Code'
        });
        if (!outputPath || outputPath.length === 0) { return; }
        
        // Check if xregistry tool is available
        if (!await checkXRegistryTool(context, outputChannel)) { return; }
        
        const outputDir = outputPath[0].fsPath;
                const command = `xregistry generate --language java --style kafkaproducer --definitions "${filePath}" --output "${outputDir}" --projectname "${projectName}"`; 
        executeCommand(command, outputPath[0], outputChannel);
    }));
    disposables.push(vscode.commands.registerCommand('xregistry.generate-java-mqttclient', async (uri: vscode.Uri) => {
        const filePath = uri.fsPath;
        
        // Only process .xreg.json files
        if (!filePath.endsWith('.xreg.json')) {
            vscode.window.showWarningMessage('This command requires a .xreg.json file');
            return;
        }
        
        // Ask for project name (mandatory)
        const fileBaseName = path.basename(filePath, path.extname(filePath));
        const projectName = await vscode.window.showInputBox({ 
            prompt: 'Enter project name',
            value: fileBaseName,
            validateInput: (value) => {
                return value && value.trim().length > 0 ? null : 'Project name is required';
            }
        });
        if (!projectName) { return; }
        
        // Ask for output directory (mandatory)
        const outputPathSuggestion = path.join(path.dirname(filePath), '{input_file_name}-java-mqttclient'.replace('{input_file_name}', fileBaseName));
        const outputPath = await vscode.window.showOpenDialog({ 
            defaultUri: vscode.Uri.file(outputPathSuggestion), 
            canSelectFiles: false,
            canSelectFolders: true,
            canSelectMany: false,
            openLabel: 'Select Output Directory',
            title: 'Select Output Directory for Generated Code'
        });
        if (!outputPath || outputPath.length === 0) { return; }
        
        // Check if xregistry tool is available
        if (!await checkXRegistryTool(context, outputChannel)) { return; }
        
        const outputDir = outputPath[0].fsPath;
                const command = `xregistry generate --language java --style mqttclient --definitions "${filePath}" --output "${outputDir}" --projectname "${projectName}"`; 
        executeCommand(command, outputPath[0], outputChannel);
    }));
    disposables.push(vscode.commands.registerCommand('xregistry.generate-java-sbconsumer', async (uri: vscode.Uri) => {
        const filePath = uri.fsPath;
        
        // Only process .xreg.json files
        if (!filePath.endsWith('.xreg.json')) {
            vscode.window.showWarningMessage('This command requires a .xreg.json file');
            return;
        }
        
        // Ask for project name (mandatory)
        const fileBaseName = path.basename(filePath, path.extname(filePath));
        const projectName = await vscode.window.showInputBox({ 
            prompt: 'Enter project name',
            value: fileBaseName,
            validateInput: (value) => {
                return value && value.trim().length > 0 ? null : 'Project name is required';
            }
        });
        if (!projectName) { return; }
        
        // Ask for output directory (mandatory)
        const outputPathSuggestion = path.join(path.dirname(filePath), '{input_file_name}-java-sbconsumer'.replace('{input_file_name}', fileBaseName));
        const outputPath = await vscode.window.showOpenDialog({ 
            defaultUri: vscode.Uri.file(outputPathSuggestion), 
            canSelectFiles: false,
            canSelectFolders: true,
            canSelectMany: false,
            openLabel: 'Select Output Directory',
            title: 'Select Output Directory for Generated Code'
        });
        if (!outputPath || outputPath.length === 0) { return; }
        
        // Check if xregistry tool is available
        if (!await checkXRegistryTool(context, outputChannel)) { return; }
        
        const outputDir = outputPath[0].fsPath;
                const command = `xregistry generate --language java --style sbconsumer --definitions "${filePath}" --output "${outputDir}" --projectname "${projectName}"`; 
        executeCommand(command, outputPath[0], outputChannel);
    }));
    disposables.push(vscode.commands.registerCommand('xregistry.generate-java-sbproducer', async (uri: vscode.Uri) => {
        const filePath = uri.fsPath;
        
        // Only process .xreg.json files
        if (!filePath.endsWith('.xreg.json')) {
            vscode.window.showWarningMessage('This command requires a .xreg.json file');
            return;
        }
        
        // Ask for project name (mandatory)
        const fileBaseName = path.basename(filePath, path.extname(filePath));
        const projectName = await vscode.window.showInputBox({ 
            prompt: 'Enter project name',
            value: fileBaseName,
            validateInput: (value) => {
                return value && value.trim().length > 0 ? null : 'Project name is required';
            }
        });
        if (!projectName) { return; }
        
        // Ask for output directory (mandatory)
        const outputPathSuggestion = path.join(path.dirname(filePath), '{input_file_name}-java-sbproducer'.replace('{input_file_name}', fileBaseName));
        const outputPath = await vscode.window.showOpenDialog({ 
            defaultUri: vscode.Uri.file(outputPathSuggestion), 
            canSelectFiles: false,
            canSelectFolders: true,
            canSelectMany: false,
            openLabel: 'Select Output Directory',
            title: 'Select Output Directory for Generated Code'
        });
        if (!outputPath || outputPath.length === 0) { return; }
        
        // Check if xregistry tool is available
        if (!await checkXRegistryTool(context, outputChannel)) { return; }
        
        const outputDir = outputPath[0].fsPath;
                const command = `xregistry generate --language java --style sbproducer --definitions "${filePath}" --output "${outputDir}" --projectname "${projectName}"`; 
        executeCommand(command, outputPath[0], outputChannel);
    }));
    disposables.push(vscode.commands.registerCommand('xregistry.generate-cs-amqpconsumer', async (uri: vscode.Uri) => {
        const filePath = uri.fsPath;
        
        // Only process .xreg.json files
        if (!filePath.endsWith('.xreg.json')) {
            vscode.window.showWarningMessage('This command requires a .xreg.json file');
            return;
        }
        
        // Ask for project name (mandatory)
        const fileBaseName = path.basename(filePath, path.extname(filePath));
        const projectName = await vscode.window.showInputBox({ 
            prompt: 'Enter project name',
            value: fileBaseName,
            validateInput: (value) => {
                return value && value.trim().length > 0 ? null : 'Project name is required';
            }
        });
        if (!projectName) { return; }
        
        // Ask for output directory (mandatory)
        const outputPathSuggestion = path.join(path.dirname(filePath), '{input_file_name}-cs-amqpconsumer'.replace('{input_file_name}', fileBaseName));
        const outputPath = await vscode.window.showOpenDialog({ 
            defaultUri: vscode.Uri.file(outputPathSuggestion), 
            canSelectFiles: false,
            canSelectFolders: true,
            canSelectMany: false,
            openLabel: 'Select Output Directory',
            title: 'Select Output Directory for Generated Code'
        });
        if (!outputPath || outputPath.length === 0) { return; }
        
        // Check if xregistry tool is available
        if (!await checkXRegistryTool(context, outputChannel)) { return; }
        
        const outputDir = outputPath[0].fsPath;
                const command = `xregistry generate --language cs --style amqpconsumer --definitions "${filePath}" --output "${outputDir}" --projectname "${projectName}"`; 
        executeCommand(command, outputPath[0], outputChannel);
    }));
    disposables.push(vscode.commands.registerCommand('xregistry.generate-cs-amqpproducer', async (uri: vscode.Uri) => {
        const filePath = uri.fsPath;
        
        // Only process .xreg.json files
        if (!filePath.endsWith('.xreg.json')) {
            vscode.window.showWarningMessage('This command requires a .xreg.json file');
            return;
        }
        
        // Ask for project name (mandatory)
        const fileBaseName = path.basename(filePath, path.extname(filePath));
        const projectName = await vscode.window.showInputBox({ 
            prompt: 'Enter project name',
            value: fileBaseName,
            validateInput: (value) => {
                return value && value.trim().length > 0 ? null : 'Project name is required';
            }
        });
        if (!projectName) { return; }
        
        // Ask for output directory (mandatory)
        const outputPathSuggestion = path.join(path.dirname(filePath), '{input_file_name}-cs-amqpproducer'.replace('{input_file_name}', fileBaseName));
        const outputPath = await vscode.window.showOpenDialog({ 
            defaultUri: vscode.Uri.file(outputPathSuggestion), 
            canSelectFiles: false,
            canSelectFolders: true,
            canSelectMany: false,
            openLabel: 'Select Output Directory',
            title: 'Select Output Directory for Generated Code'
        });
        if (!outputPath || outputPath.length === 0) { return; }
        
        // Check if xregistry tool is available
        if (!await checkXRegistryTool(context, outputChannel)) { return; }
        
        const outputDir = outputPath[0].fsPath;
                const command = `xregistry generate --language cs --style amqpproducer --definitions "${filePath}" --output "${outputDir}" --projectname "${projectName}"`; 
        executeCommand(command, outputPath[0], outputChannel);
    }));
    disposables.push(vscode.commands.registerCommand('xregistry.generate-cs-egproducer', async (uri: vscode.Uri) => {
        const filePath = uri.fsPath;
        
        // Only process .xreg.json files
        if (!filePath.endsWith('.xreg.json')) {
            vscode.window.showWarningMessage('This command requires a .xreg.json file');
            return;
        }
        
        // Ask for project name (mandatory)
        const fileBaseName = path.basename(filePath, path.extname(filePath));
        const projectName = await vscode.window.showInputBox({ 
            prompt: 'Enter project name',
            value: fileBaseName,
            validateInput: (value) => {
                return value && value.trim().length > 0 ? null : 'Project name is required';
            }
        });
        if (!projectName) { return; }
        
        // Ask for output directory (mandatory)
        const outputPathSuggestion = path.join(path.dirname(filePath), '{input_file_name}-cs-egproducer'.replace('{input_file_name}', fileBaseName));
        const outputPath = await vscode.window.showOpenDialog({ 
            defaultUri: vscode.Uri.file(outputPathSuggestion), 
            canSelectFiles: false,
            canSelectFolders: true,
            canSelectMany: false,
            openLabel: 'Select Output Directory',
            title: 'Select Output Directory for Generated Code'
        });
        if (!outputPath || outputPath.length === 0) { return; }
        
        // Check if xregistry tool is available
        if (!await checkXRegistryTool(context, outputChannel)) { return; }
        
        const outputDir = outputPath[0].fsPath;
                const command = `xregistry generate --language cs --style egproducer --definitions "${filePath}" --output "${outputDir}" --projectname "${projectName}"`; 
        executeCommand(command, outputPath[0], outputChannel);
    }));
    disposables.push(vscode.commands.registerCommand('xregistry.generate-cs-ehconsumer', async (uri: vscode.Uri) => {
        const filePath = uri.fsPath;
        
        // Only process .xreg.json files
        if (!filePath.endsWith('.xreg.json')) {
            vscode.window.showWarningMessage('This command requires a .xreg.json file');
            return;
        }
        
        // Ask for project name (mandatory)
        const fileBaseName = path.basename(filePath, path.extname(filePath));
        const projectName = await vscode.window.showInputBox({ 
            prompt: 'Enter project name',
            value: fileBaseName,
            validateInput: (value) => {
                return value && value.trim().length > 0 ? null : 'Project name is required';
            }
        });
        if (!projectName) { return; }
        
        // Ask for output directory (mandatory)
        const outputPathSuggestion = path.join(path.dirname(filePath), '{input_file_name}-cs-ehconsumer'.replace('{input_file_name}', fileBaseName));
        const outputPath = await vscode.window.showOpenDialog({ 
            defaultUri: vscode.Uri.file(outputPathSuggestion), 
            canSelectFiles: false,
            canSelectFolders: true,
            canSelectMany: false,
            openLabel: 'Select Output Directory',
            title: 'Select Output Directory for Generated Code'
        });
        if (!outputPath || outputPath.length === 0) { return; }
        
        // Check if xregistry tool is available
        if (!await checkXRegistryTool(context, outputChannel)) { return; }
        
        const outputDir = outputPath[0].fsPath;
                const command = `xregistry generate --language cs --style ehconsumer --definitions "${filePath}" --output "${outputDir}" --projectname "${projectName}"`; 
        executeCommand(command, outputPath[0], outputChannel);
    }));
    disposables.push(vscode.commands.registerCommand('xregistry.generate-cs-ehproducer', async (uri: vscode.Uri) => {
        const filePath = uri.fsPath;
        
        // Only process .xreg.json files
        if (!filePath.endsWith('.xreg.json')) {
            vscode.window.showWarningMessage('This command requires a .xreg.json file');
            return;
        }
        
        // Ask for project name (mandatory)
        const fileBaseName = path.basename(filePath, path.extname(filePath));
        const projectName = await vscode.window.showInputBox({ 
            prompt: 'Enter project name',
            value: fileBaseName,
            validateInput: (value) => {
                return value && value.trim().length > 0 ? null : 'Project name is required';
            }
        });
        if (!projectName) { return; }
        
        // Ask for output directory (mandatory)
        const outputPathSuggestion = path.join(path.dirname(filePath), '{input_file_name}-cs-ehproducer'.replace('{input_file_name}', fileBaseName));
        const outputPath = await vscode.window.showOpenDialog({ 
            defaultUri: vscode.Uri.file(outputPathSuggestion), 
            canSelectFiles: false,
            canSelectFolders: true,
            canSelectMany: false,
            openLabel: 'Select Output Directory',
            title: 'Select Output Directory for Generated Code'
        });
        if (!outputPath || outputPath.length === 0) { return; }
        
        // Check if xregistry tool is available
        if (!await checkXRegistryTool(context, outputChannel)) { return; }
        
        const outputDir = outputPath[0].fsPath;
                const command = `xregistry generate --language cs --style ehproducer --definitions "${filePath}" --output "${outputDir}" --projectname "${projectName}"`; 
        executeCommand(command, outputPath[0], outputChannel);
    }));
    disposables.push(vscode.commands.registerCommand('xregistry.generate-cs-kafkaconsumer', async (uri: vscode.Uri) => {
        const filePath = uri.fsPath;
        
        // Only process .xreg.json files
        if (!filePath.endsWith('.xreg.json')) {
            vscode.window.showWarningMessage('This command requires a .xreg.json file');
            return;
        }
        
        // Ask for project name (mandatory)
        const fileBaseName = path.basename(filePath, path.extname(filePath));
        const projectName = await vscode.window.showInputBox({ 
            prompt: 'Enter project name',
            value: fileBaseName,
            validateInput: (value) => {
                return value && value.trim().length > 0 ? null : 'Project name is required';
            }
        });
        if (!projectName) { return; }
        
        // Ask for output directory (mandatory)
        const outputPathSuggestion = path.join(path.dirname(filePath), '{input_file_name}-cs-kafkaconsumer'.replace('{input_file_name}', fileBaseName));
        const outputPath = await vscode.window.showOpenDialog({ 
            defaultUri: vscode.Uri.file(outputPathSuggestion), 
            canSelectFiles: false,
            canSelectFolders: true,
            canSelectMany: false,
            openLabel: 'Select Output Directory',
            title: 'Select Output Directory for Generated Code'
        });
        if (!outputPath || outputPath.length === 0) { return; }
        
        // Check if xregistry tool is available
        if (!await checkXRegistryTool(context, outputChannel)) { return; }
        
        const outputDir = outputPath[0].fsPath;
                const command = `xregistry generate --language cs --style kafkaconsumer --definitions "${filePath}" --output "${outputDir}" --projectname "${projectName}"`; 
        executeCommand(command, outputPath[0], outputChannel);
    }));
    disposables.push(vscode.commands.registerCommand('xregistry.generate-cs-kafkaproducer', async (uri: vscode.Uri) => {
        const filePath = uri.fsPath;
        
        // Only process .xreg.json files
        if (!filePath.endsWith('.xreg.json')) {
            vscode.window.showWarningMessage('This command requires a .xreg.json file');
            return;
        }
        
        // Ask for project name (mandatory)
        const fileBaseName = path.basename(filePath, path.extname(filePath));
        const projectName = await vscode.window.showInputBox({ 
            prompt: 'Enter project name',
            value: fileBaseName,
            validateInput: (value) => {
                return value && value.trim().length > 0 ? null : 'Project name is required';
            }
        });
        if (!projectName) { return; }
        
        // Ask for output directory (mandatory)
        const outputPathSuggestion = path.join(path.dirname(filePath), '{input_file_name}-cs-kafkaproducer'.replace('{input_file_name}', fileBaseName));
        const outputPath = await vscode.window.showOpenDialog({ 
            defaultUri: vscode.Uri.file(outputPathSuggestion), 
            canSelectFiles: false,
            canSelectFolders: true,
            canSelectMany: false,
            openLabel: 'Select Output Directory',
            title: 'Select Output Directory for Generated Code'
        });
        if (!outputPath || outputPath.length === 0) { return; }
        
        // Check if xregistry tool is available
        if (!await checkXRegistryTool(context, outputChannel)) { return; }
        
        const outputDir = outputPath[0].fsPath;
                const command = `xregistry generate --language cs --style kafkaproducer --definitions "${filePath}" --output "${outputDir}" --projectname "${projectName}"`; 
        executeCommand(command, outputPath[0], outputChannel);
    }));
    disposables.push(vscode.commands.registerCommand('xregistry.generate-cs-mqttclient', async (uri: vscode.Uri) => {
        const filePath = uri.fsPath;
        
        // Only process .xreg.json files
        if (!filePath.endsWith('.xreg.json')) {
            vscode.window.showWarningMessage('This command requires a .xreg.json file');
            return;
        }
        
        // Ask for project name (mandatory)
        const fileBaseName = path.basename(filePath, path.extname(filePath));
        const projectName = await vscode.window.showInputBox({ 
            prompt: 'Enter project name',
            value: fileBaseName,
            validateInput: (value) => {
                return value && value.trim().length > 0 ? null : 'Project name is required';
            }
        });
        if (!projectName) { return; }
        
        // Ask for output directory (mandatory)
        const outputPathSuggestion = path.join(path.dirname(filePath), '{input_file_name}-cs-mqttclient'.replace('{input_file_name}', fileBaseName));
        const outputPath = await vscode.window.showOpenDialog({ 
            defaultUri: vscode.Uri.file(outputPathSuggestion), 
            canSelectFiles: false,
            canSelectFolders: true,
            canSelectMany: false,
            openLabel: 'Select Output Directory',
            title: 'Select Output Directory for Generated Code'
        });
        if (!outputPath || outputPath.length === 0) { return; }
        
        // Check if xregistry tool is available
        if (!await checkXRegistryTool(context, outputChannel)) { return; }
        
        const outputDir = outputPath[0].fsPath;
                const command = `xregistry generate --language cs --style mqttclient --definitions "${filePath}" --output "${outputDir}" --projectname "${projectName}"`; 
        executeCommand(command, outputPath[0], outputChannel);
    }));
    disposables.push(vscode.commands.registerCommand('xregistry.generate-cs-sbconsumer', async (uri: vscode.Uri) => {
        const filePath = uri.fsPath;
        
        // Only process .xreg.json files
        if (!filePath.endsWith('.xreg.json')) {
            vscode.window.showWarningMessage('This command requires a .xreg.json file');
            return;
        }
        
        // Ask for project name (mandatory)
        const fileBaseName = path.basename(filePath, path.extname(filePath));
        const projectName = await vscode.window.showInputBox({ 
            prompt: 'Enter project name',
            value: fileBaseName,
            validateInput: (value) => {
                return value && value.trim().length > 0 ? null : 'Project name is required';
            }
        });
        if (!projectName) { return; }
        
        // Ask for output directory (mandatory)
        const outputPathSuggestion = path.join(path.dirname(filePath), '{input_file_name}-cs-sbconsumer'.replace('{input_file_name}', fileBaseName));
        const outputPath = await vscode.window.showOpenDialog({ 
            defaultUri: vscode.Uri.file(outputPathSuggestion), 
            canSelectFiles: false,
            canSelectFolders: true,
            canSelectMany: false,
            openLabel: 'Select Output Directory',
            title: 'Select Output Directory for Generated Code'
        });
        if (!outputPath || outputPath.length === 0) { return; }
        
        // Check if xregistry tool is available
        if (!await checkXRegistryTool(context, outputChannel)) { return; }
        
        const outputDir = outputPath[0].fsPath;
                const command = `xregistry generate --language cs --style sbconsumer --definitions "${filePath}" --output "${outputDir}" --projectname "${projectName}"`; 
        executeCommand(command, outputPath[0], outputChannel);
    }));
    disposables.push(vscode.commands.registerCommand('xregistry.generate-cs-sbproducer', async (uri: vscode.Uri) => {
        const filePath = uri.fsPath;
        
        // Only process .xreg.json files
        if (!filePath.endsWith('.xreg.json')) {
            vscode.window.showWarningMessage('This command requires a .xreg.json file');
            return;
        }
        
        // Ask for project name (mandatory)
        const fileBaseName = path.basename(filePath, path.extname(filePath));
        const projectName = await vscode.window.showInputBox({ 
            prompt: 'Enter project name',
            value: fileBaseName,
            validateInput: (value) => {
                return value && value.trim().length > 0 ? null : 'Project name is required';
            }
        });
        if (!projectName) { return; }
        
        // Ask for output directory (mandatory)
        const outputPathSuggestion = path.join(path.dirname(filePath), '{input_file_name}-cs-sbproducer'.replace('{input_file_name}', fileBaseName));
        const outputPath = await vscode.window.showOpenDialog({ 
            defaultUri: vscode.Uri.file(outputPathSuggestion), 
            canSelectFiles: false,
            canSelectFolders: true,
            canSelectMany: false,
            openLabel: 'Select Output Directory',
            title: 'Select Output Directory for Generated Code'
        });
        if (!outputPath || outputPath.length === 0) { return; }
        
        // Check if xregistry tool is available
        if (!await checkXRegistryTool(context, outputChannel)) { return; }
        
        const outputDir = outputPath[0].fsPath;
                const command = `xregistry generate --language cs --style sbproducer --definitions "${filePath}" --output "${outputDir}" --projectname "${projectName}"`; 
        executeCommand(command, outputPath[0], outputChannel);
    }));
    disposables.push(vscode.commands.registerCommand('xregistry.generate-cs-egazfn', async (uri: vscode.Uri) => {
        const filePath = uri.fsPath;
        
        // Only process .xreg.json files
        if (!filePath.endsWith('.xreg.json')) {
            vscode.window.showWarningMessage('This command requires a .xreg.json file');
            return;
        }
        
        // Ask for project name (mandatory)
        const fileBaseName = path.basename(filePath, path.extname(filePath));
        const projectName = await vscode.window.showInputBox({ 
            prompt: 'Enter project name',
            value: fileBaseName,
            validateInput: (value) => {
                return value && value.trim().length > 0 ? null : 'Project name is required';
            }
        });
        if (!projectName) { return; }
        
        // Ask for output directory (mandatory)
        const outputPathSuggestion = path.join(path.dirname(filePath), '{input_file_name}-cs-egazfn'.replace('{input_file_name}', fileBaseName));
        const outputPath = await vscode.window.showOpenDialog({ 
            defaultUri: vscode.Uri.file(outputPathSuggestion), 
            canSelectFiles: false,
            canSelectFolders: true,
            canSelectMany: false,
            openLabel: 'Select Output Directory',
            title: 'Select Output Directory for Generated Code'
        });
        if (!outputPath || outputPath.length === 0) { return; }
        
        // Check if xregistry tool is available
        if (!await checkXRegistryTool(context, outputChannel)) { return; }
        
        const outputDir = outputPath[0].fsPath;
                const command = `xregistry generate --language cs --style egazfn --definitions "${filePath}" --output "${outputDir}" --projectname "${projectName}"`; 
        executeCommand(command, outputPath[0], outputChannel);
    }));
    disposables.push(vscode.commands.registerCommand('xregistry.generate-cs-ehazfn', async (uri: vscode.Uri) => {
        const filePath = uri.fsPath;
        
        // Only process .xreg.json files
        if (!filePath.endsWith('.xreg.json')) {
            vscode.window.showWarningMessage('This command requires a .xreg.json file');
            return;
        }
        
        // Ask for project name (mandatory)
        const fileBaseName = path.basename(filePath, path.extname(filePath));
        const projectName = await vscode.window.showInputBox({ 
            prompt: 'Enter project name',
            value: fileBaseName,
            validateInput: (value) => {
                return value && value.trim().length > 0 ? null : 'Project name is required';
            }
        });
        if (!projectName) { return; }
        
        // Ask for output directory (mandatory)
        const outputPathSuggestion = path.join(path.dirname(filePath), '{input_file_name}-cs-ehazfn'.replace('{input_file_name}', fileBaseName));
        const outputPath = await vscode.window.showOpenDialog({ 
            defaultUri: vscode.Uri.file(outputPathSuggestion), 
            canSelectFiles: false,
            canSelectFolders: true,
            canSelectMany: false,
            openLabel: 'Select Output Directory',
            title: 'Select Output Directory for Generated Code'
        });
        if (!outputPath || outputPath.length === 0) { return; }
        
        // Check if xregistry tool is available
        if (!await checkXRegistryTool(context, outputChannel)) { return; }
        
        const outputDir = outputPath[0].fsPath;
                const command = `xregistry generate --language cs --style ehazfn --definitions "${filePath}" --output "${outputDir}" --projectname "${projectName}"`; 
        executeCommand(command, outputPath[0], outputChannel);
    }));
    disposables.push(vscode.commands.registerCommand('xregistry.generate-cs-sbazfn', async (uri: vscode.Uri) => {
        const filePath = uri.fsPath;
        
        // Only process .xreg.json files
        if (!filePath.endsWith('.xreg.json')) {
            vscode.window.showWarningMessage('This command requires a .xreg.json file');
            return;
        }
        
        // Ask for project name (mandatory)
        const fileBaseName = path.basename(filePath, path.extname(filePath));
        const projectName = await vscode.window.showInputBox({ 
            prompt: 'Enter project name',
            value: fileBaseName,
            validateInput: (value) => {
                return value && value.trim().length > 0 ? null : 'Project name is required';
            }
        });
        if (!projectName) { return; }
        
        // Ask for output directory (mandatory)
        const outputPathSuggestion = path.join(path.dirname(filePath), '{input_file_name}-cs-sbazfn'.replace('{input_file_name}', fileBaseName));
        const outputPath = await vscode.window.showOpenDialog({ 
            defaultUri: vscode.Uri.file(outputPathSuggestion), 
            canSelectFiles: false,
            canSelectFolders: true,
            canSelectMany: false,
            openLabel: 'Select Output Directory',
            title: 'Select Output Directory for Generated Code'
        });
        if (!outputPath || outputPath.length === 0) { return; }
        
        // Check if xregistry tool is available
        if (!await checkXRegistryTool(context, outputChannel)) { return; }
        
        const outputDir = outputPath[0].fsPath;
                const command = `xregistry generate --language cs --style sbazfn --definitions "${filePath}" --output "${outputDir}" --projectname "${projectName}"`; 
        executeCommand(command, outputPath[0], outputChannel);
    }));
    disposables.push(vscode.commands.registerCommand('xregistry.generate-asyncapi-consumer', async (uri: vscode.Uri) => {
        const filePath = uri.fsPath;
        
        // Only process .xreg.json files
        if (!filePath.endsWith('.xreg.json')) {
            vscode.window.showWarningMessage('This command requires a .xreg.json file');
            return;
        }
        
        // Ask for project name (mandatory)
        const fileBaseName = path.basename(filePath, path.extname(filePath));
        const projectName = await vscode.window.showInputBox({ 
            prompt: 'Enter project name',
            value: fileBaseName,
            validateInput: (value) => {
                return value && value.trim().length > 0 ? null : 'Project name is required';
            }
        });
        if (!projectName) { return; }
        
        // Ask for output directory (mandatory)
        const outputPathSuggestion = path.join(path.dirname(filePath), '{input_file_name}-asyncapi-consumer.yaml'.replace('{input_file_name}', fileBaseName));
        const outputPath = await vscode.window.showOpenDialog({ 
            defaultUri: vscode.Uri.file(outputPathSuggestion), 
            canSelectFiles: false,
            canSelectFolders: true,
            canSelectMany: false,
            openLabel: 'Select Output Directory',
            title: 'Select Output Directory for Generated Code'
        });
        if (!outputPath || outputPath.length === 0) { return; }
        
        // Check if xregistry tool is available
        if (!await checkXRegistryTool(context, outputChannel)) { return; }
        
        const outputDir = outputPath[0].fsPath;
                const command = `xregistry generate --language asyncapi --style consumer --definitions "${filePath}" --output "${outputDir}" --projectname "${projectName}"`; 
        executeCommand(command, outputPath[0], outputChannel);
    }));
    disposables.push(vscode.commands.registerCommand('xregistry.generate-asyncapi-producer', async (uri: vscode.Uri) => {
        const filePath = uri.fsPath;
        
        // Only process .xreg.json files
        if (!filePath.endsWith('.xreg.json')) {
            vscode.window.showWarningMessage('This command requires a .xreg.json file');
            return;
        }
        
        // Ask for project name (mandatory)
        const fileBaseName = path.basename(filePath, path.extname(filePath));
        const projectName = await vscode.window.showInputBox({ 
            prompt: 'Enter project name',
            value: fileBaseName,
            validateInput: (value) => {
                return value && value.trim().length > 0 ? null : 'Project name is required';
            }
        });
        if (!projectName) { return; }
        
        // Ask for output directory (mandatory)
        const outputPathSuggestion = path.join(path.dirname(filePath), '{input_file_name}-asyncapi-producer.yaml'.replace('{input_file_name}', fileBaseName));
        const outputPath = await vscode.window.showOpenDialog({ 
            defaultUri: vscode.Uri.file(outputPathSuggestion), 
            canSelectFiles: false,
            canSelectFolders: true,
            canSelectMany: false,
            openLabel: 'Select Output Directory',
            title: 'Select Output Directory for Generated Code'
        });
        if (!outputPath || outputPath.length === 0) { return; }
        
        // Check if xregistry tool is available
        if (!await checkXRegistryTool(context, outputChannel)) { return; }
        
        const outputDir = outputPath[0].fsPath;
                const command = `xregistry generate --language asyncapi --style producer --definitions "${filePath}" --output "${outputDir}" --projectname "${projectName}"`; 
        executeCommand(command, outputPath[0], outputChannel);
    }));
    disposables.push(vscode.commands.registerCommand('xregistry.generate-openapi-producer', async (uri: vscode.Uri) => {
        const filePath = uri.fsPath;
        
        // Only process .xreg.json files
        if (!filePath.endsWith('.xreg.json')) {
            vscode.window.showWarningMessage('This command requires a .xreg.json file');
            return;
        }
        
        // Ask for project name (mandatory)
        const fileBaseName = path.basename(filePath, path.extname(filePath));
        const projectName = await vscode.window.showInputBox({ 
            prompt: 'Enter project name',
            value: fileBaseName,
            validateInput: (value) => {
                return value && value.trim().length > 0 ? null : 'Project name is required';
            }
        });
        if (!projectName) { return; }
        
        // Ask for output directory (mandatory)
        const outputPathSuggestion = path.join(path.dirname(filePath), '{input_file_name}-openapi-producer.yaml'.replace('{input_file_name}', fileBaseName));
        const outputPath = await vscode.window.showOpenDialog({ 
            defaultUri: vscode.Uri.file(outputPathSuggestion), 
            canSelectFiles: false,
            canSelectFolders: true,
            canSelectMany: false,
            openLabel: 'Select Output Directory',
            title: 'Select Output Directory for Generated Code'
        });
        if (!outputPath || outputPath.length === 0) { return; }
        
        // Check if xregistry tool is available
        if (!await checkXRegistryTool(context, outputChannel)) { return; }
        
        const outputDir = outputPath[0].fsPath;
                const command = `xregistry generate --language openapi --style producer --definitions "${filePath}" --output "${outputDir}" --projectname "${projectName}"`; 
        executeCommand(command, outputPath[0], outputChannel);
    }));
    disposables.push(vscode.commands.registerCommand('xregistry.generate-openapi-subscriber', async (uri: vscode.Uri) => {
        const filePath = uri.fsPath;
        
        // Only process .xreg.json files
        if (!filePath.endsWith('.xreg.json')) {
            vscode.window.showWarningMessage('This command requires a .xreg.json file');
            return;
        }
        
        // Ask for project name (mandatory)
        const fileBaseName = path.basename(filePath, path.extname(filePath));
        const projectName = await vscode.window.showInputBox({ 
            prompt: 'Enter project name',
            value: fileBaseName,
            validateInput: (value) => {
                return value && value.trim().length > 0 ? null : 'Project name is required';
            }
        });
        if (!projectName) { return; }
        
        // Ask for output directory (mandatory)
        const outputPathSuggestion = path.join(path.dirname(filePath), '{input_file_name}-openapi-subscriber.yaml'.replace('{input_file_name}', fileBaseName));
        const outputPath = await vscode.window.showOpenDialog({ 
            defaultUri: vscode.Uri.file(outputPathSuggestion), 
            canSelectFiles: false,
            canSelectFolders: true,
            canSelectMany: false,
            openLabel: 'Select Output Directory',
            title: 'Select Output Directory for Generated Code'
        });
        if (!outputPath || outputPath.length === 0) { return; }
        
        // Check if xregistry tool is available
        if (!await checkXRegistryTool(context, outputChannel)) { return; }
        
        const outputDir = outputPath[0].fsPath;
                const command = `xregistry generate --language openapi --style subscriber --definitions "${filePath}" --output "${outputDir}" --projectname "${projectName}"`; 
        executeCommand(command, outputPath[0], outputChannel);
    }));
    disposables.push(vscode.commands.registerCommand('xregistry.generate-asaql-dispatch', async (uri: vscode.Uri) => {
        const filePath = uri.fsPath;
        
        // Only process .xreg.json files
        if (!filePath.endsWith('.xreg.json')) {
            vscode.window.showWarningMessage('This command requires a .xreg.json file');
            return;
        }
        
        // Ask for project name (mandatory)
        const fileBaseName = path.basename(filePath, path.extname(filePath));
        const projectName = await vscode.window.showInputBox({ 
            prompt: 'Enter project name',
            value: fileBaseName,
            validateInput: (value) => {
                return value && value.trim().length > 0 ? null : 'Project name is required';
            }
        });
        if (!projectName) { return; }
        
        // Ask for output directory (mandatory)
        const outputPathSuggestion = path.join(path.dirname(filePath), '{input_file_name}-asaql-dispatch.asaql'.replace('{input_file_name}', fileBaseName));
        const outputPath = await vscode.window.showOpenDialog({ 
            defaultUri: vscode.Uri.file(outputPathSuggestion), 
            canSelectFiles: false,
            canSelectFolders: true,
            canSelectMany: false,
            openLabel: 'Select Output Directory',
            title: 'Select Output Directory for Generated Code'
        });
        if (!outputPath || outputPath.length === 0) { return; }
        
        // Check if xregistry tool is available
        if (!await checkXRegistryTool(context, outputChannel)) { return; }
        
        const outputDir = outputPath[0].fsPath;
                const command = `xregistry generate --language asaql --style dispatch --definitions "${filePath}" --output "${outputDir}" --projectname "${projectName}"`; 
        executeCommand(command, outputPath[0], outputChannel);
    }));
    disposables.push(vscode.commands.registerCommand('xregistry.generate-asaql-dispatchpayload', async (uri: vscode.Uri) => {
        const filePath = uri.fsPath;
        
        // Only process .xreg.json files
        if (!filePath.endsWith('.xreg.json')) {
            vscode.window.showWarningMessage('This command requires a .xreg.json file');
            return;
        }
        
        // Ask for project name (mandatory)
        const fileBaseName = path.basename(filePath, path.extname(filePath));
        const projectName = await vscode.window.showInputBox({ 
            prompt: 'Enter project name',
            value: fileBaseName,
            validateInput: (value) => {
                return value && value.trim().length > 0 ? null : 'Project name is required';
            }
        });
        if (!projectName) { return; }
        
        // Ask for output directory (mandatory)
        const outputPathSuggestion = path.join(path.dirname(filePath), '{input_file_name}-asaql-dispatchpayload.asaql'.replace('{input_file_name}', fileBaseName));
        const outputPath = await vscode.window.showOpenDialog({ 
            defaultUri: vscode.Uri.file(outputPathSuggestion), 
            canSelectFiles: false,
            canSelectFolders: true,
            canSelectMany: false,
            openLabel: 'Select Output Directory',
            title: 'Select Output Directory for Generated Code'
        });
        if (!outputPath || outputPath.length === 0) { return; }
        
        // Check if xregistry tool is available
        if (!await checkXRegistryTool(context, outputChannel)) { return; }
        
        const outputDir = outputPath[0].fsPath;
                const command = `xregistry generate --language asaql --style dispatchpayload --definitions "${filePath}" --output "${outputDir}" --projectname "${projectName}"`; 
        executeCommand(command, outputPath[0], outputChannel);
    }));
    context.subscriptions.push(...disposables);
}

export function deactivate() {}
