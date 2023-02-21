// file: src/webview/main.ts

import { provideVSCodeDesignSystem, vsCodeButton, Button, TextField, Dropdown, vsCodeTextField, vsCodeDropdown, vsCodeOption, vsCodeDivider } from "@vscode/webview-ui-toolkit";
import { WebviewOptions, Webview } from "vscode";
import { WebviewApi } from "vscode-webview";


provideVSCodeDesignSystem().register(vsCodeButton(), vsCodeTextField(), vsCodeDropdown(), vsCodeOption(), vsCodeDivider());

const vscode = acquireVsCodeApi();

window.addEventListener("load", main);

function main() {
  // To get improved type annotations/IntelliSense the associated class for
  // a given toolkit component can be imported and used to type cast a reference
  // to the element (i.e. the `as Button` syntax)
    const form = document.getElementById('submit') as Button;
    form?.addEventListener('click', handleFormSubmit);
    const definition = document.getElementById('definition') as TextField;
    definition?.addEventListener('change', handleDefinitionChange);
    const projectName = document.getElementById('projectName') as TextField;
    projectName?.addEventListener('change', handleProjectNameChange);
    const pickDefinition = document.getElementById('pickDefinition') as Button;
    pickDefinition?.addEventListener('click', handlePickDefinitionChange);
    const pickOutput = document.getElementById('pickOutput') as Button;
    pickOutput?.addEventListener('click', handlePickOutputChange);
    const language = document.getElementById('language') as Dropdown;
    language?.addEventListener('change', handleLanguageChange);
    const style = document.getElementById('style') as Dropdown;
    style?.addEventListener('change', handleStyleChange);

    language.selectFirstOption();
    handleLanguageChange.call(language, new Event('change'));
}

function handleLanguageChange(this: HTMLElement, event: Event) {
    const language = document.getElementById('language') as Dropdown;
    const style = document.getElementById('style') as Dropdown;
    var optionsData = document.getElementById('optionsData')?.firstChild as Text;
    var options = JSON.parse(optionsData.data);    
    if (language && style &&
        options.hasOwnProperty(language.value) &&
        options[language.value].hasOwnProperty("templates")) {
        let templates = []
        for (var key in options[language.value].templates) {
            templates.push(options[language.value].templates[key])
        }
        // inverse sort the templates by priority
        templates = templates.sort((a, b) => a.priority < b.priority ? 1 :  a.priority == b.priority? 0 : -1);           
        let optionsHTML = templates.map((template) => {
            return '<option value="' + template.name + '">' + (template.description?template.description:template.name) + '</option>';
        }).join('');
        style.innerHTML = optionsHTML;
    }
}

 function handleDefinitionChange(this: HTMLElement, event: Event) {
     const definition = document.getElementById('definition') as HTMLInputElement;
     if (definition.value.length > 0) {
         if (definition.value.startsWith('http://') || definition.value.startsWith('https://') || definition.value.startsWith('file://') ||
             definition.value) {
             return;
         }
     }
    vscode.postMessage({
        command: 'error',
        message: 'The definition must be a URI or existing file name'
    });
};


function handleFormSubmit(this: Button, event: Event) {
    event.preventDefault();
    const data = new FormData(this.form as HTMLFormElement);
    vscode.postMessage({
        command: 'generate',
        definitions: data.get('definition'),
        projectName: data.get('projectName'),
        language: data.get('language'),
        style: data.get('style'),
        output: data.get('output')
    });
}


function handleProjectNameChange(this: HTMLElement, ev: Event) {
    
}

window.addEventListener('message', event => {
    const message = event.data; // The JSON data from the extension
    switch (message.command) {
        case 'resultDialogForDefinition':
            let definition = document.getElementById('definition') as HTMLInputElement;
            if (definition) {
                definition.value = message.definitionsFile;
            }
            break;
        case 'resultDialogForOutput':
            let output = document.getElementById('output') as HTMLInputElement;
            if (output) {
                output.value = message.output;
            }
    }
});

function handlePickDefinitionChange(this: HTMLElement, ev: Event) {
    let definition = this.ownerDocument.getElementById('definition') as TextField;
    if (definition) {
        vscode.postMessage({
            command: 'openDialogForDefinition',
            definitions: definition.value
        });        
    }
}

function handlePickOutputChange(this: HTMLElement, ev: Event) {
    let output = document.getElementById('output') as TextField;
    if (output) {
        vscode.postMessage({
            command: 'openDialogForOutput',
            output: output.value
        });
    };
}

function handleStyleChange(this: HTMLElement, ev: Event) {
  
}

