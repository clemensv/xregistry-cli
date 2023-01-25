import * as vscode from 'vscode';
import * as fs from 'fs';
import * as path from 'path';
import * as child_process from 'child_process';
import { CodeGeneratorWizardPanel } from "./panels/CodeGeneratorWizardPanel";
import internal from 'stream';

export function activate(context: vscode.ExtensionContext) {

    let pythonInstalled = true;
    try {
        child_process.execSync('python --version');
    } catch (err) {
        pythonInstalled = false;
    }

    if (!pythonInstalled) {
        vscode.window.showInformationMessage(`Python is not installed or it is not in the PATH. Do you want to install it now?`, 'Yes', 'No').then((answer) => {
            if (answer === 'Yes') {
                // Open the link to download python
                vscode.commands.executeCommand('vscode.open', vscode.Uri.parse('https://www.python.org/downloads/'));
            }
        });
        return;
    }

    let packageLocation = '';
    let packageName = 'cedisco-codegen';
    let packageInstalled = false;
    do {
        try {
            const output = child_process.execSync(`pip show ${packageName}`).toString();
            const match = output.match(/^Location: (.+)$/m);
            if (match) {
                packageLocation = match[1];
                packageInstalled = true;
            } else {
                packageInstalled = false;
                return;
            }
        } catch (err) {
            packageInstalled = false;
            return;
        }

        if (!packageInstalled) {
            vscode.window.showInformationMessage(`The package "${packageName}" is not installed. Do you want to install it now?`, 'Yes', 'No').then((answer) => {
                if (answer === 'Yes') {
                    child_process.execSync(`pip install ${packageName}`);
                } else {
                    return;
                }
            });
        }
    } while (!packageInstalled);

    let scriptLocation = path.join(packageLocation, "cedisco_codegen", "cedisco_codegen.py");
        
    let options: { [key: string]: { description: string, templates: { [key: string]: { description: string, priority: number, name: string } } } } = {};
    const templateLocation = path.join(packageLocation, "cedisco_codegen", "templates");
    let languages = fs.readdirSync(templateLocation, { withFileTypes: true }).filter((dirent) => dirent.isDirectory()).map((dirent) => dirent.name);
    for (let i = 0; i < languages.length; i++) {
        let infoPath = path.join(templateLocation, languages[i], "_templateinfo.json");
        let description = languages[i];
        if (fs.existsSync(infoPath)) {
            // read the JSON file and parse the "description" property
            let info = JSON.parse(fs.readFileSync(infoPath, 'utf8'));
            if (info.hasOwnProperty("description")) {
                description = info.description;
            }
        }
        options[languages[i]] = { description: description, templates: {} };

        let templates = fs.readdirSync(path.join(packageLocation, "cedisco_codegen", "templates", languages[i]), { withFileTypes: true }).filter((dirent) => dirent.isDirectory()).map((dirent) => dirent.name );
        // remove the _schemas folder from the list
        templates = templates.filter((style) => {
            return style !== "_schemas";
        });
        if (templates.length > 0) {
            for (let j = 0; j < templates.length; j++) {
                let description = templates[j];
                let priority = 100;
                let infoPath = path.join(templateLocation, languages[i], templates[j], "_templateinfo.json");
                if (fs.existsSync(infoPath)) {
                    // read the JSON file and parse the "description" property
                    let info = JSON.parse(fs.readFileSync(infoPath, 'utf8'));
                    if (info.hasOwnProperty("description")) {
                        description = info.description;
                    }
                    if (info.hasOwnProperty("priority")) {
                        priority = info.priority;
                    }
                }
                options[languages[i]].templates[templates[j]] = { description: description, priority: priority, name: templates[j] };
            }
        }
    }

    let disposable = vscode.commands.registerCommand('cedisco-codegen.generate', async () => {
        let definitionsFile = "";
        let editor = vscode.window.activeTextEditor;
        if (editor) {
            let isCloudEventsDiscovery = false;
            let document = editor.document;
            if (document.languageId === "json" || document.languageId === "cedisco" || document.languageId === "plaintext") {
                definitionsFile = document.fileName;
                try {
                    let jsonData = JSON.parse(document.getText());
                    if (jsonData.hasOwnProperty("$schema") &&
                        jsonData.hasOwnProperty("specversion")
                        && (jsonData.hasOwnProperty("endpoints") || jsonData.hasOwnProperty("groups") || jsonData.hasOwnProperty("schemagroups"))) {
                        isCloudEventsDiscovery = true;
                    }
                    else if (jsonData.hasOwnProperty("endpoint") || jsonData.hasOwnProperty("group") || jsonData.hasOwnProperty("schemagroup")) {
                        isCloudEventsDiscovery = true;
                    }
                    else {
                        for (let key in jsonData) {
                            if (jsonData[key].hasOwnProperty("type") &&
                                (jsonData[key]["type"] === "endpoint" || jsonData[key]["type"] === "group") || jsonData[key]["type"] === "schemagroup") {
                                isCloudEventsDiscovery = true;
                                break;
                            }
                        }
                    }
                } catch (error) {
                    isCloudEventsDiscovery = false;
                }
            }
            if (isCloudEventsDiscovery) {
                definitionsFile = document.fileName;
            }
        }

        CodeGeneratorWizardPanel.render(context.extensionUri, definitionsFile, options, scriptLocation);

    });
    context.subscriptions.push(disposable);

    disposable = vscode.commands.registerCommand('cedisco-codegen.file-actions',
        (filePath) => {
            let definitionsFile = "";
            if (filePath) {
                definitionsFile = filePath.fsPath;
            }
            CodeGeneratorWizardPanel.render(context.extensionUri, definitionsFile, options, scriptLocation);
        });
    context.subscriptions.push(disposable);
    
}
