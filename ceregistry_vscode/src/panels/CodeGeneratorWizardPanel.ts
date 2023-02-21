
import * as vscode from "vscode";
import { getUri } from "../utilities/getUri";
import { getNonce } from "../utilities/getNonce";
import * as path from 'path';
import * as child_process from 'child_process';
import * as fs from 'fs';

export class CodeGeneratorWizardPanel {
    public static currentPanel: CodeGeneratorWizardPanel | undefined;
    private readonly _panel: vscode.WebviewPanel;
    private _disposables: vscode.Disposable[] = [];
    

    private constructor(
        panel: vscode.WebviewPanel,
        extensionUri: vscode.Uri,
        definitionsFile: string,
        options: { [key: string]: { description: string, templates: { [key: string]: { description: string, priority: number, name: string } } } }) {
        this._panel = panel;
        this._panel.webview.html = this._getWebviewContent(this._panel.webview, extensionUri, definitionsFile, options);
        this._panel.onDidDispose(() => this.dispose(), null, this._disposables);
        this._setWebviewMessageListener(this._panel.webview);
    }

    public static render(
        extensionUri: vscode.Uri,
        definitionsFile: string,
        options: { [key: string]: { description: string, templates: { [key: string]: { description: string, priority: number, name: string } } } })
    {
        if (CodeGeneratorWizardPanel.currentPanel)
        {
            CodeGeneratorWizardPanel.currentPanel._panel.reveal(vscode.ViewColumn.One);
        }
        else
        {
            const panel = vscode.window.createWebviewPanel("codegen-wizard", "CloudEvents Code Generator", vscode.ViewColumn.One, {
                // Enable javascript in the webview
                enableScripts: true,
                // Restrict the webview to only load resources from the `out` directory
                localResourceRoots: [vscode.Uri.joinPath(extensionUri, 'out')]
            });

            CodeGeneratorWizardPanel.currentPanel = new CodeGeneratorWizardPanel(panel, extensionUri, definitionsFile, options);
        }
    }

    public dispose() {
        CodeGeneratorWizardPanel.currentPanel = undefined;

        this._panel.dispose();

        while (this._disposables.length) {
            const disposable = this._disposables.pop();
            if (disposable) {
                disposable.dispose();
            }
        }
    }

    private _setWebviewMessageListener(webview: vscode.Webview) {
        webview.onDidReceiveMessage(
            (message: any) => {
                const command = message.command;
                const text = message.text;

                switch (command) {
                    case 'generate':
                        let definitions = message.definitions;
                        let projectName = message.projectName;
                        let language = message.language;
                        let style = message.style;
                        let output = message.output;

                        if (definitions.length == 0) {
                            vscode.window.showErrorMessage("Select a definitions file");
                            return;
                        }
                        if (projectName.length == 0) {
                            vscode.window.showErrorMessage("Enter a project name");
                            return;
                        }
                        if (language.length == 0) {
                            vscode.window.showErrorMessage("Select a language");
                            return;
                        }
                        if (style.length == 0) {
                            vscode.window.showErrorMessage("Select a style");
                            return;
                        }
                        if (output.length == 0) {
                            vscode.window.showErrorMessage("Select an output folder");
                            return;
                        }

                        // strip any problematic shell characters from input
                        if (definitions.indexOf(/["]/g) != -1) {
                            vscode.window.showErrorMessage("Definitions file path contains invalid characters");
                            return;
                        }
                        if (projectName.indexOf(/[\s;|&<>$(){}]/g) != -1) {
                            vscode.window.showErrorMessage("Project name contains invalid characters");
                            return;
                        }
                        if (language.indexOf(/[\s;|&<>$(){}]/g) != -1) {
                            vscode.window.showErrorMessage("Language contains invalid characters");
                            return;
                        }
                        if (style.indexOf(/[\s;|&<>$(){}]/g) != -1) {
                            vscode.window.showErrorMessage("Style contains invalid characters");
                            return;
                        }
                        if (output.indexOf(/["]/g) != -1) {
                            vscode.window.showErrorMessage("Output path contains invalid characters");
                            return;
                        }

                        // if the output directory exists and is not empty, ask the user if they want to proceed
                        let fileExists = fs.existsSync(output);
                        if (fileExists) {
                            let files = fs.readdirSync(output);
                            if (files.length > 0) {
                                vscode.window.showInformationMessage(`The output directory is not empty. Proceed?`, 'Yes', 'No').then(result => {
                                    if (result == 'No') {
                                        return;
                                    }
                                    this.callCodeGenerator(output, projectName, style, language, definitions);
                                });
                                return;
                            }
                        }
                        // otherwise, just call the code generator
                        this.callCodeGenerator(output, projectName, style, language, definitions);
                        break;
                    
                    case 'openDialogForDefinition':

                        vscode.window.showOpenDialog({
                            canSelectFiles: true,
                            canSelectFolders: false,
                            canSelectMany: false,
                            openLabel: "Select definitions file",
                            defaultUri: vscode.Uri.file(path.dirname(message.definitions)),
                            filters: {
                                "DISCO": ["disco", "yaml.disco"]
                            }
                        }).then((fileUri) => {
                            if (fileUri && fileUri.length > 0) {
                                try {
                                    child_process.execSync(`ceregistry validate --definitions "${fileUri[0].fsPath}"`);
                                } catch (error: Error | any) {
                                    vscode.window.showErrorMessage("Invalid or malformed definitions file");
                                    return;
                                }
                                webview.postMessage({
                                    command: 'resultDialogForDefinition',
                                    definitionsFile: fileUri[0].fsPath
                                }); 
                            }
                        });
                        break;
                    case 'openDialogForOutput':
                        vscode.window.showOpenDialog({
                            canSelectFiles: false,
                            canSelectFolders: true,
                            canSelectMany: false,

                            openLabel: "Select output folder",
                            defaultUri: vscode.Uri.file(path.dirname(message.output)),
                        }).then((fileUri) => {
                            if (fileUri && fileUri.length > 0) {
                                webview.postMessage({
                                    command: 'resultDialogForOutput',
                                    output: fileUri[0].fsPath
                                });
                            }
                        });
                        break;
                    case 'checkOutput':
                        let outputFolder = message.output;
                        if (outputFolder.length > 0) {
                            // check whether folder exists and is empty
                            let fileExists = fs.existsSync(outputFolder);
                            if (fileExists) {
                                let files = fs.readdirSync(outputFolder);
                                if (files.length > 0) {
                                    vscode.window.showWarningMessage("The output folder is not empty. The code generator will overwrite existing files.");
                                }
                            }
                            webview.postMessage({
                                command: 'resultCheckOutput',
                                output: outputFolder,
                                exists: fileExists
                            });
                        }
                    case 'cancel':
                            this.dispose();
                            break;
                    case 'error':
                            vscode.window.showErrorMessage(message.error);
                            break;
                }
            },
            undefined,
            this._disposables
        );
    }

    private callCodeGenerator(output: any, projectName: any, style: any, language: any, definitions: any) {
        try {
            child_process.execSync(`ceregistry generate --output "${output}" --projectname "${projectName}" --style "${style}" --language "${language}" --definitions "${definitions}"`);
            vscode.window.showInformationMessage("Code generation completed.", "Open Folder")
                .then(selection => {
                    if (selection === "Open Folder") {
                        vscode.commands.executeCommand('vscode.openFolder', vscode.Uri.file(output), {"forceNewWindow": true});
                    }
            });
        }
        catch (error: any) {
            vscode.window.showInformationMessage(error.toString());
        }
    }

    private _getWebviewContent(
        webview: vscode.Webview,
        extensionUri: vscode.Uri,
        definitionsFile: string,
        options: { [key: string]: { description: string, templates: { [key: string]: { description: string, priority: number, name: string } } } }): string {
        const webviewUri = getUri(webview, extensionUri, ["out", "webview.js"]);
        const styleUri = getUri(webview, extensionUri, ["out", "style.css"]);
        const codiconUri = getUri(webview, extensionUri, ["out", "codicon.css"]);
        const nonce = getNonce();

        let htmlWizard = 
        /*html*/`<!DOCTYPE html>
        <html>
            <head>
                <meta charset="UTF-8">
                <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src ${webview.cspSource} 'unsafe-inline'; font-src ${webview.cspSource}; img-src ${webview.cspSource} https:; script-src 'nonce-${nonce}' 'unsafe-eval' 'unsafe-inline';">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <link rel="stylesheet" href="${styleUri}">
                <link rel="stylesheet" href="${codiconUri}">
                <title>CloudEvents Discovery Code Generator</title>
                <script type="module" nonce="${nonce}" src="${webviewUri}"></script>            
            </head>
            <body>
            <span id="optionsData"><!-- ${JSON.stringify(options)} --></span>
                <div class="control-container">
                    <div class="header">
                        <h1>CloudEvents Discovery Tool</h1>
                        <p>This wizard helps you validate specifications or creating code for producing or consuming CloudEvents with the CloudEvents SDK. The wizard wraps the "ceregistry" tool that uses CloudEvents Discovery registry endpoints or documents as input. The code generator always (re-)creates full projects (assemblies, modules, packages, depending on the nomenclature of the chosen language) that you can easily integrate into your own code-bases.</p>
                    </div>
                    <vscode-divider></vscode-divider>
                    <div class="content">
                        <form id="form">
                            <section class="component-control">
                                <vscode-text-field id="definition" name="definition" value="${definitionsFile}" required size="80" type="url">
                                    CloudEvents Discovery document source.
                                    <section slot="end" style="display:flex; align-items: center;"> 
                                        <vscode-button class="component-companion" id="pickDefinition" appearance="icon">
                                          <span class="codicon codicon-search"></span>
                                        </vscode-button>
                                    </section>
                                </vscode-text-field>
                            </section>
                            <section class="component-control">
                                <vscode-text-field id="projectName" name="projectName" value="" required size="80">
                                    Name of the output project. This name is used for project files names and namespaces as applicable
                                </vscode-text-field>
                            </section>
                            <section class="component-control">
                            <vscode-text-field id="output" name="output" required size="80">
                                Output directory
                                <section slot="end" style="display:flex; align-items: center;">
                                    <vscode-button id="pickOutput" appearance="icon">
                                        <span class="codicon codicon-search"></span>
                                    </vscode-button>    
                                </section>
                            </vscode-text-field>
                            </section>
                            
                            <section class="component-control">
                                Programming language/runtime<br/>
                                <vscode-dropdown id="language" name="language" position="below" required>
                                    ${Object.keys(options).map((key) => {
                                    return `<vscode-option value="${key}">${options[key].description?options[key].description:key}</vscode-option>`;
                                }).join('')
                                }
                                </vscode-dropdown>
                            </section>
                            <section class="component-control">
                                The style of template to choose for the code generator for the chosen language option<br/>
                                <vscode-dropdown id="style" name="style" position="below" required></vscode-dropdown>
                            </section>
                           
                            <section class="component-control">
                                <vscode-button id="submit" appearance="primary">
                                    Generate Code
                                </vscode-button>
                            </section>
                        </form>
                    </div>
                </div>
            
        </body>
        </html>`;
        return htmlWizard;
    }
}