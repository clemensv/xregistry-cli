import * as vscode from 'vscode';
import * as fs from 'fs';
import * as path from 'path';
import * as child_process from 'child_process';
import { CodeGeneratorWizardPanel } from "./panels/CodeGeneratorWizardPanel";
import internal from 'stream';

export function activate(context: vscode.ExtensionContext) {

    let toolInstalled = true;

    let langsStyles: Array<{ name: string; description: string; priority: number; styles: Array<{ name: string; description: string; priority: number }> }> = new Array();
    try {
        // call the CLI tool with the list --format=json option and see if it works
        // take the stdout and parse it as JSON
        let output = child_process.execSync('xregistry list --format=json', { encoding: 'utf8' });
        langsStyles = JSON.parse(output);
    } catch (err) {
        toolInstalled = false;
    }

    if (!toolInstalled) {
        let callback = async () => {
            vscode.window.showInformationMessage(`The "xregistry CLI tool" is not installed. Please install it and then reload the window.`);
        }
        let disposable = vscode.commands.registerCommand('xregistry.ui', callback);
        context.subscriptions.push(disposable);
        return;
    }

    let options: { [key: string]: { description: string, templates: { [key: string]: { description: string, priority: number, name: string } } } } = {};

    // map langStyles to options
    for (let lang of langsStyles.sort((a, b) => a.priority - b.priority)) {
        options[lang.name] = { description: lang.description, templates: {} };
        for (let style of lang.styles.sort((a, b) => a.priority - b.priority)) {
            options[lang.name].templates[style.name] = { description: style.description, priority: style.priority, name: style.name };
        }        
    }

    let disposable = vscode.commands.registerCommand('xregistry.ui', async (filePath) => {
        let definitionsFile = filePath ? filePath.fsPath : "";
        
        if (!filePath) {
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
                            && (jsonData.hasOwnProperty("endpoints") || jsonData.hasOwnProperty("definitionGroups") || jsonData.hasOwnProperty("schemaGroups"))) {
                            isCloudEventsDiscovery = true;
                        }
                        else if (jsonData.hasOwnProperty("endpoint") || jsonData.hasOwnProperty("definitiongroup") || jsonData.hasOwnProperty("schemagroup")) {
                            isCloudEventsDiscovery = true;
                        }
                        else {
                            for (let key in jsonData) {
                                if (jsonData[key].hasOwnProperty("type") &&
                                    (jsonData[key]["type"] === "endpoint" || jsonData[key]["type"] === "definitiongroup") || jsonData[key]["type"] === "schemagroup") {
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
        }

        let projectName = "";
        let outputFile = vscode.workspace.workspaceFolders?path.join(vscode.workspace.workspaceFolders[0].uri.fsPath, "generated"):"";

        CodeGeneratorWizardPanel.render(context.extensionUri, definitionsFile, projectName, outputFile, options);

    });
    context.subscriptions.push(disposable);
}
